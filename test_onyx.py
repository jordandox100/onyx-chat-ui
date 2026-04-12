#!/usr/bin/env python3
"""ONYX Test Suite — validates Letta-first architecture"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    print("\n=== Testing Imports ===")
    ok = True
    for name, stmt in [
        ("PySide6",       "import PySide6"),
        ("piper-tts",     "from piper import PiperVoice"),
        ("dotenv",        "from dotenv import load_dotenv"),
        ("supabase",      "from supabase import create_client"),
        ("letta-client",  "from letta_client import Letta"),
    ]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError as e:
            print(f"  [FAIL] {name}: {e}")
            ok = False
    for name, stmt in [("torch", "import torch"), ("whisper", "import whisper"), ("pyaudio", "import pyaudio")]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [WARN] {name} (optional)")
    return ok


def test_no_direct_anthropic():
    """Verify no direct Anthropic SDK usage in the app (Letta owns model calls)."""
    print("\n=== Testing: No Direct Anthropic ===")
    import importlib
    ok = True

    # chat_service must NOT import anthropic
    src = Path("desktop_app/services/chat_service.py").read_text()
    if "import anthropic" in src or "from anthropic" in src:
        print("  [FAIL] chat_service.py still imports anthropic SDK directly")
        ok = False
    else:
        print("  [OK] chat_service.py: no direct anthropic import")

    if "client.messages.create" in src:
        print("  [FAIL] chat_service.py still calls Anthropic API directly")
        ok = False
    else:
        print("  [OK] chat_service.py: no direct API call")

    return ok


def test_no_brain_in_storage():
    """Verify storage_service has no persona/prompt/brain logic."""
    print("\n=== Testing: No Brain in Storage ===")
    src = Path("desktop_app/services/storage_service.py").read_text()
    ok = True

    for bad in ["DEFAULT_PERSONALITY", "DEFAULT_KNOWLEDGEBASE", "DEFAULT_USER_PROFILE",
                 "DEFAULT_INSTRUCTIONS", "build_system_message", "get_personality",
                 "get_knowledgebase", "get_user_profile", "get_instructions"]:
        if bad in src:
            print(f"  [FAIL] storage_service.py still contains '{bad}'")
            ok = False

    if ok:
        print("  [OK] storage_service.py: no persona/prompt/brain logic")

    # Must still have SQLite mirror
    for need in ["add_message", "get_chat_messages", "create_chat", "get_settings"]:
        if need not in src:
            print(f"  [FAIL] storage_service.py missing '{need}'")
            ok = False

    if ok:
        print("  [OK] storage_service.py: has SQLite mirror + settings")
    return ok


def test_deleted_files():
    """Verify Letta-duplicating files are gone."""
    print("\n=== Testing: Dead Files Removed ===")
    ok = True
    for f in ["desktop_app/services/context_service.py",
              "desktop_app/services/personality_service.py",
              "desktop_app/services/tool_service.py"]:
        if Path(f).exists():
            print(f"  [FAIL] {f} still exists (should be deleted)")
            ok = False
        else:
            print(f"  [OK] {f} deleted")
    return ok


def test_storage():
    print("\n=== Testing Storage (Mirror Only) ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService()
        s.initialize()
        cid = s.create_chat("Test")
        s.add_message(cid, "user", "hi")
        s.add_message(cid, "assistant", "hello")
        msgs = s.get_chat_messages(cid)
        assert len(msgs) == 2
        print(f"  [OK] Message mirror ({len(msgs)} msgs)")

        count = s.get_message_count(cid)
        assert count == 2
        print(f"  [OK] message_count = {count}")

        page = s.get_messages_page(cid, 0, 1)
        assert len(page) == 1
        print(f"  [OK] paginated loading")

        settings = s.get_settings()
        assert "tts" in settings
        print(f"  [OK] settings")

        s.delete_chat(cid)
        print("  [OK] delete")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_chat_service():
    print("\n=== Testing Chat Service ===")
    try:
        from desktop_app.services.chat_service import ChatService, ANTHROPIC_MODELS

        cs = ChatService()
        assert cs.runtime_name == "not_configured"
        print(f"  [OK] runtime = {cs.runtime_name} (no bridge)")

        for name, mid, desc in ANTHROPIC_MODELS:
            assert mid.startswith("anthropic/"), f"Bad prefix: {mid}"
        print(f"  [OK] {len(ANTHROPIC_MODELS)} models with anthropic/ prefix")

        # Must NOT have ToolService
        import inspect
        src = inspect.getsource(ChatService)
        assert "ToolService" not in src
        assert "tool_service" not in src
        assert "build_system" not in src
        print("  [OK] No ToolService, no prompt building")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_letta_bridge():
    print("\n=== Testing Letta Bridge ===")
    try:
        from desktop_app.services.letta_bridge import LettaBridge

        bridge = LettaBridge()
        assert not bridge.available
        assert not bridge.agent_ready
        print(f"  [OK] Status: {bridge.status} — {bridge.status_detail}")

        health = bridge.health_check()
        assert health["ok"] is False
        print(f"  [OK] Health check: clean failure")

        state = bridge.get_agent_state()
        assert state["status"] in ("NOT_CONFIGURED", "NOT_INSTALLED")
        print(f"  [OK] Agent state: {state['status']}")

        result = bridge.send_message("test")
        assert "not ready" in result["response"].lower()
        print("  [OK] send_message: clean error when not configured")

        blocks = bridge.get_memory_blocks()
        assert blocks == []
        print("  [OK] Memory blocks: empty (not connected)")

        # Bridge must NOT read local persona/config
        import inspect
        src = inspect.getsource(LettaBridge)
        assert "get_personality" not in src
        assert "build_system_message" not in src
        assert "get_knowledgebase" not in src
        print("  [OK] Bridge does not read local persona/config")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_supabase_service():
    print("\n=== Testing Supabase Service ===")
    try:
        from desktop_app.services.supabase_service import SupabaseService
        svc = SupabaseService()
        print(f"  [OK] Status: {svc.status_text}")
        assert svc.get_conversations() == []
        assert svc.get_tasks() == []
        print("  [OK] Graceful fallback")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_env_vars():
    print("\n=== Testing Env Vars ===")
    env_path = Path(".env")
    if not env_path.exists():
        print("  [FAIL] .env missing")
        return False
    content = env_path.read_text()
    required = ["LETTA_BASE_URL", "LETTA_API_KEY", "LETTA_AGENT_ID",
                "ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
    ok = True
    for var in required:
        if var in content:
            print(f"  [OK] {var}")
        else:
            print(f"  [FAIL] {var} missing from .env")
            ok = False
    return ok


def test_tts():
    print("\n=== Testing TTS ===")
    try:
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        voices = tts.available_voices
        print(f"  [OK] {len(voices)} voices")
        tts.speed = 1.5
        assert tts.speed == 1.5
        tts.speed = 1.0
        print("  [OK] speed control")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_code_blocks():
    print("\n=== Testing Code Block Parsing ===")
    try:
        from desktop_app.ui.chat_widget import parse_segments, text_for_tts
        text = "Code:\n```python\nprint('hi')\n```\nDone."
        store = {}
        segs = parse_segments(text, store)
        assert len(segs) == 3
        assert segs[1]["type"] == "code"
        tts = text_for_tts(text)
        assert "print" not in tts
        print("  [OK] code block parsing + TTS exclusion")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_ui_components():
    print("\n=== Testing UI Components ===")
    try:
        from desktop_app.ui.styles import MAIN_STYLE, LOAD_MORE_HTML
        assert "inspectorPanel" in MAIN_STYLE
        print("  [OK] styles")
        from desktop_app.ui.chat_widget import ChatWidget
        from desktop_app.ui.inspector_panel import InspectorPanel
        from desktop_app.ui.main_window import MainWindow
        from desktop_app.ui.avatar_widget import RobotAvatar
        print("  [OK] all UI widgets importable")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_directories():
    print("\n=== Testing Directories ===")
    ok = True
    for d in ["Onyx", "Onyx/history", "Onyx/config", "Onyx/logs", "Onyx/voices"]:
        if Path(d).exists():
            print(f"  [OK] {d}")
        else:
            print(f"  [FAIL] {d}")
            ok = False
    return ok


def main():
    print("\n" + "=" * 56)
    print("       ONYX Test Suite (Letta-first architecture)")
    print("=" * 56)

    tests = [
        ("Imports",              test_imports),
        ("No Direct Anthropic",  test_no_direct_anthropic),
        ("No Brain in Storage",  test_no_brain_in_storage),
        ("Dead Files Removed",   test_deleted_files),
        ("Env Vars",             test_env_vars),
        ("Directories",          test_directories),
        ("Storage Mirror",       test_storage),
        ("Chat Service",         test_chat_service),
        ("Letta Bridge",         test_letta_bridge),
        ("Supabase Service",     test_supabase_service),
        ("TTS",                  test_tts),
        ("Code Blocks",          test_code_blocks),
        ("UI Components",        test_ui_components),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [CRASH] {name}: {e}")
            results[name] = False

    print("\n" + "=" * 56)
    print("                    SUMMARY")
    print("=" * 56)
    passed = sum(1 for v in results.values() if v)
    for n, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}: {n}")
    print(f"\n  {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
