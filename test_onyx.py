#!/usr/bin/env python3
"""ONYX Test Suite — Supabase + Anthropic runtime, conditional tools, no Letta"""
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
            exec(stmt); print(f"  [OK] {name}")
        except ImportError as e:
            print(f"  [FAIL] {name}: {e}"); ok = False
    return ok


def test_no_letta():
    print("\n=== Testing: No Letta ===")
    ok = True
    for f in ["desktop_app/services/runtime.py", "desktop_app/services/chat_service.py",
              "desktop_app/main.py", "desktop_app/ui/inspector_panel.py",
              "desktop_app/ui/main_window.py"]:
        src = Path(f).read_text()
        if "from letta" in src or "import letta" in src or "LettaBridge" in src:
            print(f"  [FAIL] {f} imports Letta"); ok = False
    if ok: print("  [OK] No Letta imports")
    if Path("desktop_app/services/letta_bridge.py").exists():
        print("  [FAIL] letta_bridge.py still exists"); ok = False
    else:
        print("  [OK] letta_bridge.py deleted")
    env = Path(".env").read_text()
    if "LETTA_" in env:
        print("  [FAIL] .env still has LETTA_ vars"); ok = False
    else:
        print("  [OK] .env clean")
    return ok


def test_tool_router():
    print("\n=== Testing Tool Router ===")
    try:
        from desktop_app.services.tool_router import (
            classify_tool_need, select_tool_bundle,
            ROUTE_DIRECT, ROUTE_WEB, ROUTE_MEMORY, ROUTE_FILE, ROUTE_CODE,
        )

        # Direct answer (no tools)
        assert classify_tool_need("explain quantum computing") == ROUTE_DIRECT
        assert classify_tool_need("rewrite this paragraph") == ROUTE_DIRECT
        assert classify_tool_need("what is 2+2") == ROUTE_DIRECT
        print("  [OK] direct_answer routing (no tools)")

        # Web
        assert classify_tool_need("search online for Python 4 release") == ROUTE_WEB
        assert classify_tool_need("what's the latest news") == ROUTE_WEB
        print("  [OK] web_lookup routing")

        # Memory
        assert classify_tool_need("do you remember my project?") == ROUTE_MEMORY
        assert classify_tool_need("what did I say last time") == ROUTE_MEMORY
        print("  [OK] memory_lookup routing")

        # File
        assert classify_tool_need("read the file /etc/hosts") == ROUTE_FILE
        assert classify_tool_need("show me /home/user/config.yaml") == ROUTE_FILE
        print("  [OK] file_lookup routing")

        # Code
        assert classify_tool_need("run python test.py") == ROUTE_CODE
        assert classify_tool_need("debug this traceback") == ROUTE_CODE
        print("  [OK] code_work routing")

        # Bundles
        assert select_tool_bundle(ROUTE_DIRECT) == []
        assert len(select_tool_bundle(ROUTE_WEB)) == 1
        assert len(select_tool_bundle(ROUTE_FILE)) == 2
        assert len(select_tool_bundle(ROUTE_CODE)) == 3
        print("  [OK] tool bundles: direct=0, web=1, file=2, code=3")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tool_executor():
    print("\n=== Testing Tool Executor ===")
    try:
        from desktop_app.services.tool_executor import execute_tool_call

        # Shell exec
        result = execute_tool_call("shell_exec", {"command": "echo hello123"})
        assert "hello123" in result
        print("  [OK] shell_exec")

        # File read
        result = execute_tool_call("file_read", {"path": "/app/.env"})
        assert "ANTHROPIC_API_KEY" in result
        print("  [OK] file_read")

        # File search
        result = execute_tool_call("file_search",
                                   {"pattern": "*.py", "directory": "/app/desktop_app/services"})
        assert "runtime.py" in result
        print("  [OK] file_search")

        # Unknown tool
        result = execute_tool_call("nonexistent", {})
        assert "Unknown" in result
        print("  [OK] unknown tool handled")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_runtime_no_tools_default():
    print("\n=== Testing Runtime (no tools default) ===")
    try:
        from desktop_app.services.runtime import OnyxRuntime
        import inspect

        rt = OnyxRuntime()
        state = rt.get_agent_state()
        assert state["runtime"] == "supabase+anthropic"
        print(f"  [OK] Status: {state['status']}")

        # Verify no tools parameter in direct path
        src = inspect.getsource(OnyxRuntime._execute_direct)
        assert "tools=" not in src
        print("  [OK] _execute_direct: no tools= parameter")

        # Verify tools only in _execute_with_tools
        src2 = inspect.getsource(OnyxRuntime._execute_with_tools)
        assert "tools=tools" in src2
        print("  [OK] _execute_with_tools: tools parameter present")

        # Verify router is used in send_message
        src3 = inspect.getsource(OnyxRuntime.send_message)
        assert "classify_tool_need" in src3
        assert "select_tool_bundle" in src3
        print("  [OK] send_message uses router")

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
        assert len(ANTHROPIC_MODELS) >= 10
        print(f"  [OK] {len(ANTHROPIC_MODELS)} models")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_storage():
    print("\n=== Testing Storage ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService(); s.initialize()
        cid = s.create_chat("Test")
        s.add_message(cid, "user", "hi")
        assert s.get_message_count(cid) == 1
        s.delete_chat(cid)
        print("  [OK] SQLite mirror")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_supabase_service():
    print("\n=== Testing Supabase Service ===")
    try:
        from desktop_app.services.supabase_service import SupabaseService
        svc = SupabaseService()
        assert svc.get_memories() == []
        assert svc.get_beliefs() == []
        assert svc.get_goals() == []
        print(f"  [OK] Status: {svc.status_text}, graceful fallback")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_ui_components():
    print("\n=== Testing UI Components ===")
    try:
        from desktop_app.ui.chat_widget import ChatWidget
        from desktop_app.ui.inspector_panel import InspectorPanel
        from desktop_app.ui.main_window import MainWindow
        import inspect
        src = inspect.getsource(InspectorPanel)
        assert "bridge" not in src
        src2 = inspect.getsource(MainWindow)
        assert "bridge" not in src2
        print("  [OK] No bridge/letta in UI")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_env_vars():
    print("\n=== Testing Env Vars ===")
    env = Path(".env").read_text()
    ok = True
    for v in ["ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]:
        if v in env: print(f"  [OK] {v}")
        else: print(f"  [FAIL] {v} missing"); ok = False
    for bad in ["LETTA_BASE_URL", "LETTA_API_KEY"]:
        if bad in env: print(f"  [FAIL] {bad} in .env"); ok = False
    return ok


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
    print("\n" + "=" * 60)
    print("  ONYX Tests (Supabase+Anthropic, Conditional Tools, No Letta)")
    print("=" * 60)

    tests = [
        ("Imports",               test_imports),
        ("No Letta",              test_no_letta),
        ("Env Vars",              test_env_vars),
        ("Tool Router",           test_tool_router),
        ("Tool Executor",         test_tool_executor),
        ("Runtime (no tools)",    test_runtime_no_tools_default),
        ("Chat Service",          test_chat_service),
        ("Storage",               test_storage),
        ("Supabase Service",      test_supabase_service),
        ("UI Components",         test_ui_components),
        ("TTS",                   test_tts),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [CRASH] {name}: {e}"); results[name] = False

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    for n, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}: {n}")
    print(f"\n  {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
