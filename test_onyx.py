#!/usr/bin/env python3
"""ONYX Test Suite — Supabase + Anthropic runtime, no Letta"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    print("\n=== Testing Imports ===")
    ok = True
    for name, stmt in [
        ("PySide6",    "import PySide6"),
        ("anthropic",  "import anthropic"),
        ("piper-tts",  "from piper import PiperVoice"),
        ("dotenv",     "from dotenv import load_dotenv"),
        ("supabase",   "from supabase import create_client"),
    ]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError as e:
            print(f"  [FAIL] {name}: {e}")
            ok = False
    for name, stmt in [("torch", "import torch"), ("whisper", "import whisper")]:
        try:
            exec(stmt); print(f"  [OK] {name}")
        except ImportError:
            print(f"  [WARN] {name} (optional)")
    return ok


def test_no_letta():
    """Verify zero Letta dependency in active code."""
    print("\n=== Testing: No Letta ===")
    ok = True
    for f in ["desktop_app/services/runtime.py", "desktop_app/services/chat_service.py",
              "desktop_app/main.py", "desktop_app/ui/inspector_panel.py",
              "desktop_app/ui/main_window.py"]:
        src = Path(f).read_text()
        if "from letta" in src or "import letta" in src or "LettaBridge" in src:
            print(f"  [FAIL] {f} still imports Letta")
            ok = False
    if ok:
        print("  [OK] No Letta imports in active code")

    deleted = Path("desktop_app/services/letta_bridge.py")
    if deleted.exists():
        print("  [FAIL] letta_bridge.py still exists")
        ok = False
    else:
        print("  [OK] letta_bridge.py deleted")

    env = Path(".env").read_text()
    if "LETTA_" in env:
        print("  [FAIL] .env still has LETTA_ vars")
        ok = False
    else:
        print("  [OK] .env clean of LETTA vars")

    reqs = Path("requirements.txt").read_text()
    if "letta" in reqs.lower():
        print("  [FAIL] requirements.txt still has letta")
        ok = False
    else:
        print("  [OK] requirements.txt clean of letta")

    return ok


def test_runtime():
    print("\n=== Testing Runtime ===")
    try:
        from desktop_app.services.runtime import OnyxRuntime
        rt = OnyxRuntime()
        state = rt.get_agent_state()
        assert state["runtime"] == "supabase+anthropic"
        print(f"  [OK] Status: {state['status']}")
        print(f"  [OK] Runtime: {state['runtime']}")

        # Without API key, should return clean error
        result = rt.send_message("test", conversation_id=1)
        assert "not ready" in result["response"].lower() or "not configured" in result["response"].lower() or "error" in result["response"].lower()
        print("  [OK] send_message: clean failure without key")

        # No transcript replay in source
        import inspect
        src = inspect.getsource(OnyxRuntime)
        assert "history[-20:]" not in src
        assert "get_chat_messages" not in src
        print("  [OK] No transcript replay in runtime")

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
        print(f"  [OK] runtime = {cs.runtime_name}")

        for name, mid, desc in ANTHROPIC_MODELS:
            assert not mid.startswith("anthropic/"), f"Should not have anthropic/ prefix: {mid}"
        print(f"  [OK] {len(ANTHROPIC_MODELS)} models (raw IDs, no prefix)")

        import inspect
        src = inspect.getsource(ChatService)
        assert "bridge" not in src.lower()
        assert "letta" not in src.lower()
        print("  [OK] No bridge/letta references")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_storage():
    print("\n=== Testing Storage ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService()
        s.initialize()
        cid = s.create_chat("Test")
        s.add_message(cid, "user", "hi")
        s.add_message(cid, "assistant", "hello")
        assert s.get_message_count(cid) == 2
        assert len(s.get_messages_page(cid, 0, 1)) == 1
        s.delete_chat(cid)
        print("  [OK] SQLite mirror works")

        import inspect
        src = inspect.getsource(StorageService)
        assert "personality" not in src.lower()
        assert "knowledgebase" not in src.lower()
        assert "build_system" not in src.lower()
        print("  [OK] No brain logic in storage")
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
        assert svc.get_memories() == []
        assert svc.get_beliefs() == []
        assert svc.get_goals() == []
        assert svc.get_tasks() == []
        assert svc.get_events() == []
        print("  [OK] All methods return safe defaults when unconfigured")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_env_vars():
    print("\n=== Testing Env Vars ===")
    env = Path(".env").read_text()
    ok = True
    for var in ["ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]:
        if var in env:
            print(f"  [OK] {var}")
        else:
            print(f"  [FAIL] {var} missing"); ok = False
    for bad in ["LETTA_BASE_URL", "LETTA_API_KEY", "LETTA_AGENT_ID"]:
        if bad in env:
            print(f"  [FAIL] {bad} still in .env"); ok = False
    if ok:
        print("  [OK] No stale Letta vars")
    return ok


def test_ui_components():
    print("\n=== Testing UI Components ===")
    try:
        from desktop_app.ui.styles import MAIN_STYLE, LOAD_MORE_HTML
        from desktop_app.ui.chat_widget import ChatWidget
        from desktop_app.ui.inspector_panel import InspectorPanel
        from desktop_app.ui.main_window import MainWindow
        from desktop_app.ui.avatar_widget import RobotAvatar

        # Inspector must not reference bridge/letta
        import inspect
        src = inspect.getsource(InspectorPanel)
        assert "bridge" not in src
        assert "letta" not in src.lower()
        print("  [OK] Inspector: no bridge/letta")

        src2 = inspect.getsource(MainWindow)
        assert "bridge" not in src2
        assert "letta" not in src2.lower()
        print("  [OK] MainWindow: no bridge/letta")

        print("  [OK] All UI widgets importable")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_code_blocks():
    print("\n=== Testing Code Blocks ===")
    try:
        from desktop_app.ui.chat_widget import parse_segments, text_for_tts
        store = {}
        segs = parse_segments("Code:\n```python\nprint('hi')\n```\nDone.", store)
        assert len(segs) == 3 and segs[1]["type"] == "code"
        assert "print" not in text_for_tts("```python\nprint('hi')\n```\nDone.")
        print("  [OK] code blocks + TTS exclusion")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tts():
    print("\n=== Testing TTS ===")
    try:
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        print(f"  [OK] {len(tts.available_voices)} voices")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main():
    print("\n" + "=" * 56)
    print("     ONYX Test Suite (Supabase+Anthropic, No Letta)")
    print("=" * 56)

    tests = [
        ("Imports",           test_imports),
        ("No Letta",          test_no_letta),
        ("Env Vars",          test_env_vars),
        ("Runtime",           test_runtime),
        ("Chat Service",      test_chat_service),
        ("Storage",           test_storage),
        ("Supabase Service",  test_supabase_service),
        ("UI Components",     test_ui_components),
        ("Code Blocks",       test_code_blocks),
        ("TTS",               test_tts),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [CRASH] {name}: {e}"); results[name] = False

    print("\n" + "=" * 56)
    passed = sum(1 for v in results.values() if v)
    for n, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}: {n}")
    print(f"\n  {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
