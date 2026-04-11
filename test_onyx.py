#!/usr/bin/env python3
"""ONYX Test Suite — validates all services and components"""
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
    for name, stmt in [("torch", "import torch"), ("whisper", "import whisper"), ("pyaudio", "import pyaudio")]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [WARN] {name} (optional)")
    return ok


def test_storage():
    print("\n=== Testing Storage ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService()
        s.initialize()
        cid = s.create_chat("Test")
        s.add_message(cid, "user", "hi")
        s.add_message(cid, "assistant", "hello")
        msgs = s.get_chat_messages(cid)
        assert len(msgs) == 2
        print(f"  [OK] CRUD ({len(msgs)} msgs)")

        # Test new methods
        count = s.get_message_count(cid)
        assert count == 2
        print(f"  [OK] message_count = {count}")

        page = s.get_messages_page(cid, 0, 1)
        assert len(page) == 1
        print(f"  [OK] get_messages_page (1 of {count})")

        s.save_summary(cid, "Test summary", 2)
        summary = s.get_summary(cid)
        assert summary == "Test summary"
        print(f"  [OK] save/get_summary")

        s.delete_chat(cid)
        print("  [OK] delete")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_config_files():
    print("\n=== Testing Config ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService()
        s.initialize()
        for f in ["personality.txt", "knowledgebase.txt", "user.txt", "instructions.txt", "settings.json"]:
            assert (s.config_path / f).exists()
        msg = s.build_system_message()
        assert "ONYX" in msg
        print(f"  [OK] configs + system message ({len(msg)} chars)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tool_service():
    print("\n=== Testing Tools ===")
    try:
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        assert "shell" in ts.get_tools_prompt()
        test = 'Hello <tool_call type="shell">echo hi</tool_call> done'
        calls = ts.parse_tool_calls(test)
        assert len(calls) == 1
        result = ts.run_shell("echo test123")
        assert "test123" in result
        print("  [OK] tools prompt, parse, shell exec")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_chat_service():
    print("\n=== Testing Chat Service ===")
    try:
        from desktop_app.services.chat_service import ChatService, ANTHROPIC_MODELS

        # Test with default args (backward compat)
        cs = ChatService()
        for name, mid, desc in ANTHROPIC_MODELS:
            assert desc, f"Missing description: {name}"
        print(f"  [OK] {len(ANTHROPIC_MODELS)} models with descriptions")

        assert cs.model_name == "claude-sonnet-4-6"
        print("  [OK] default: claude-sonnet-4-6")

        cs.set_model("claude-opus-4-6")
        assert cs.model_name == "claude-opus-4-6"
        cs.set_model("claude-sonnet-4-6")
        print("  [OK] model switch")

        import inspect
        src = inspect.getsource(ChatService)
        assert "emergentintegrations" not in src
        assert "cancel_flag" in src
        assert "context" in src
        print("  [OK] anthropic SDK, cancel, context support")

        # Test with context service
        from desktop_app.services.storage_service import StorageService
        from desktop_app.services.context_service import ContextService
        storage = StorageService()
        storage.initialize()
        ctx = ContextService(storage)
        cs2 = ChatService(storage=storage, context_service=ctx)
        assert cs2.context is ctx
        print("  [OK] ChatService with ContextService")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_context_service():
    print("\n=== Testing Context Service ===")
    try:
        from desktop_app.services.storage_service import StorageService
        from desktop_app.services.context_service import ContextService, RECENT_WINDOW

        storage = StorageService()
        storage.initialize()
        ctx = ContextService(storage)

        # Create a chat with messages
        cid = storage.create_chat("Context Test")
        for i in range(15):
            role = "user" if i % 2 == 0 else "assistant"
            storage.add_message(cid, role, f"Message {i}")

        system = "You are ONYX."
        enhanced, messages = ctx.build_context(cid, "New question", system)

        # Should have summary in system message (15 > RECENT_WINDOW=6)
        assert "Prior Conversation Context" in enhanced
        print(f"  [OK] Summary injected into system message")

        # Messages should be RECENT_WINDOW + 1 (recent + new msg)
        assert len(messages) == RECENT_WINDOW + 1
        print(f"  [OK] Context window = {len(messages)} msgs (was 16 old approach)")

        # Token savings: 15 msgs -> 7 msgs = ~53% reduction
        print(f"  [OK] Token reduction: {15} -> {len(messages)} messages")

        # Summary should be cached
        summary = ctx.get_conversation_summary(cid)
        assert summary
        print(f"  [OK] Summary cached ({len(summary)} chars)")

        storage.delete_chat(cid)
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_supabase_service():
    print("\n=== Testing Supabase Service ===")
    try:
        from desktop_app.services.supabase_service import SupabaseService
        svc = SupabaseService()
        # Should init without error even when not configured
        status = svc.status_text
        print(f"  [OK] Status: {status}")

        # All methods should return safe defaults when not configured
        assert svc.get_conversations() == []
        assert svc.get_tasks() == []
        assert svc.get_events() == []
        assert svc.get_files() == []
        assert svc.get_agent_state() is None
        print("  [OK] Graceful fallback (all methods return safe defaults)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_letta_bridge():
    print("\n=== Testing Letta Bridge ===")
    try:
        from desktop_app.services.letta_bridge import LettaBridge
        from desktop_app.services.storage_service import StorageService
        from desktop_app.services.context_service import ContextService
        from desktop_app.services.chat_service import ChatService

        storage = StorageService()
        storage.initialize()
        ctx = ContextService(storage)
        chat = ChatService(storage=storage, context_service=ctx)
        bridge = LettaBridge(context_service=ctx, chat_service=chat)

        state = bridge.get_agent_state()
        assert state["status"] == "active"
        assert state["agent_id"] == "onyx"
        print(f"  [OK] Agent state: {state['status']}")

        mem = bridge.get_memory_summary()
        assert "conversation_summary" in mem
        print("  [OK] Memory summary structure")

        # Tasks/events return empty when no Supabase
        assert bridge.get_tasks() == []
        assert bridge.get_events() == []
        print("  [OK] Tasks/events graceful fallback")

        # Message loading
        cid = storage.create_chat("Bridge Test")
        storage.add_message(cid, "user", "hello")
        recent = bridge.load_recent_messages(cid)
        assert len(recent) == 1
        print("  [OK] load_recent_messages")

        count = bridge.get_message_count(cid)
        assert count == 1
        print("  [OK] get_message_count")

        storage.delete_chat(cid)
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tts():
    print("\n=== Testing TTS ===")
    try:
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        voices = tts.available_voices
        print(f"  [OK] {len(voices)} voices:")
        for name, _, _ in voices:
            print(f"       - {name}")

        british = [n for n, _, _ in voices if "British" in n or "Jarvis" in n]
        assert len(british) >= 2
        print(f"  [OK] {len(british)} British male voices")

        jarvis = [n for n, _, _ in voices if "Jarvis" in n]
        assert len(jarvis) == 1
        print(f"  [OK] Jarvis voice: {jarvis[0]}")

        tts.speed = 1.5
        assert tts.speed == 1.5
        tts.speed = 0.3
        assert tts.speed == 0.5
        tts.speed = 3.0
        assert tts.speed == 2.0
        tts.speed = 1.0
        print("  [OK] speed control (clamped 0.5-2.0)")

        tts.stop()
        print("  [OK] stop method")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tts_synthesis():
    print("\n=== Testing TTS Synthesis ===")
    try:
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        if not tts.available:
            print("  [SKIP] No voices")
            return True

        voices = tts.available_voices
        name, model_file, speaker_id = voices[0]
        voice = tts._load_voice(model_file)
        assert voice is not None
        print(f"  [OK] Loaded: {name}")

        import wave, tempfile
        from piper.config import SynthesisConfig
        cfg = SynthesisConfig(speaker_id=speaker_id, noise_scale=0.8, noise_w_scale=0.9)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()
        with wave.open(tmp_path, "wb") as wf:
            voice.synthesize_wav("Testing with natural voice settings.", wf, syn_config=cfg)
        size = Path(tmp_path).stat().st_size
        assert size > 1000
        print(f"  [OK] Synthesized ({size} bytes, natural settings)")
        Path(tmp_path).unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_code_blocks():
    print("\n=== Testing Code Block Parsing ===")
    try:
        from desktop_app.ui.chat_widget import parse_segments, text_for_tts

        text = "Here is code:\n```python\nprint('hello')\nx = 42\n```\nAnd more text.\n```bash\necho hi\n```\nDone."
        store = {}
        segs = parse_segments(text, store)
        assert len(segs) == 5
        assert segs[0]["type"] == "text"
        assert segs[1]["type"] == "code"
        assert segs[1]["lang"] == "python"
        assert segs[3]["type"] == "code"
        assert segs[3]["lang"] == "bash"
        assert len(store) == 2
        print(f"  [OK] Parsed {len(segs)} segments, {len(store)} code blocks")

        tts = text_for_tts(text)
        assert "print" not in tts
        assert "echo" not in tts
        assert "Here is code" in tts
        assert "Done" in tts
        print(f"  [OK] TTS excludes code blocks")

        store2 = {}
        segs2 = parse_segments("Just regular text here.", store2)
        assert len(segs2) == 1 and segs2[0]["type"] == "text"
        assert len(store2) == 0
        print("  [OK] Pure text passthrough")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_avatar():
    print("\n=== Testing Avatar ===")
    try:
        from desktop_app.ui.avatar_widget import RobotAvatar
        print("  [OK] RobotAvatar importable")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_ui_components():
    print("\n=== Testing UI Components ===")
    try:
        from desktop_app.ui.styles import (
            MAIN_STYLE, USER_MSG_HTML, AGENT_MSG_HTML, CODE_BLOCK_HTML,
            LOAD_MORE_HTML, SUMMARY_BAR_HTML, DANGER,
        )
        assert len(MAIN_STYLE) > 100
        assert "{text}" in USER_MSG_HTML
        assert "{code}" in CODE_BLOCK_HTML
        assert "{key}" in CODE_BLOCK_HTML
        assert "copy://" in CODE_BLOCK_HTML
        assert "stopButton" in MAIN_STYLE
        assert "inspectorPanel" in MAIN_STYLE
        assert "loadmore://" in LOAD_MORE_HTML
        print("  [OK] styles + templates (code blocks, stop, inspector, load-more)")

        from desktop_app.ui.chat_widget import ChatWidget, MessageInput
        print("  [OK] chat_widget")
        from desktop_app.ui.inspector_panel import InspectorPanel, CollapsibleSection
        print("  [OK] inspector_panel")
        from desktop_app.ui.main_window import MainWindow
        print("  [OK] main_window")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_icon():
    print("\n=== Testing Icon ===")
    ok = True
    for f in ["install/onyx_icon.svg", "install/onyx_icon.png"]:
        if Path(f).exists():
            print(f"  [OK] {f} ({Path(f).stat().st_size} bytes)")
        else:
            print(f"  [FAIL] {f} missing")
            ok = False
    return ok


def test_voice_models():
    print("\n=== Testing Voice Models ===")
    d = Path("Onyx/voices")
    if not d.exists():
        print("  [FAIL] directory missing")
        return False
    onnx = sorted(d.glob("*.onnx"))
    print(f"  [OK] {len(onnx)} models:")
    for f in onnx:
        print(f"       - {f.name} ({f.stat().st_size/1024/1024:.1f} MB)")
    return len(onnx) >= 4


def test_directories():
    print("\n=== Testing Directories ===")
    ok = True
    for d in ["Onyx", "Onyx/history", "Onyx/config", "Onyx/voice", "Onyx/logs", "Onyx/voices"]:
        if Path(d).exists():
            print(f"  [OK] {d}")
        else:
            print(f"  [FAIL] {d}")
            ok = False
    return ok


def main():
    print("\n" + "=" * 52)
    print("         ONYX Application Test Suite")
    print("=" * 52)

    tests = [
        ("Imports",           test_imports),
        ("Directories",       test_directories),
        ("Voice Models",      test_voice_models),
        ("Storage",           test_storage),
        ("Config",            test_config_files),
        ("Tools",             test_tool_service),
        ("Context Service",   test_context_service),
        ("Supabase Service",  test_supabase_service),
        ("Letta Bridge",      test_letta_bridge),
        ("Chat Service",      test_chat_service),
        ("TTS",               test_tts),
        ("TTS Synthesis",     test_tts_synthesis),
        ("Code Blocks",       test_code_blocks),
        ("Avatar",            test_avatar),
        ("UI Components",     test_ui_components),
        ("Icon",              test_icon),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [CRASH] {name}: {e}")
            results[name] = False

    print("\n" + "=" * 52)
    print("                  SUMMARY")
    print("=" * 52)
    passed = sum(1 for v in results.values() if v)
    for n, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}: {n}")
    print(f"\n  {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
