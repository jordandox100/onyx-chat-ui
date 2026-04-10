#!/usr/bin/env python3
"""ONYX Test Suite — validates all services and components"""
import sys
import json
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
    ]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError as e:
            print(f"  [FAIL] {name}: {e}")
            ok = False
    for name, stmt in [
        ("torch",   "import torch"),
        ("whisper", "import whisper"),
        ("pyaudio", "import pyaudio"),
    ]:
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
        print("  [OK] init")
        cid = s.create_chat("Test")
        s.add_message(cid, "user", "hi")
        s.add_message(cid, "assistant", "hello")
        msgs = s.get_chat_messages(cid)
        assert len(msgs) == 2
        print(f"  [OK] CRUD ({len(msgs)} msgs)")
        s.delete_chat(cid)
        print("  [OK] delete")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_config_files():
    print("\n=== Testing Config Files ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService()
        s.initialize()
        for f in ["personality.txt", "knowledgebase.txt", "user.txt", "instructions.txt", "settings.json"]:
            assert (s.config_path / f).exists(), f"{f} missing"
            print(f"  [OK] {f}")
        msg = s.build_system_message()
        assert "ONYX" in msg
        print(f"  [OK] system message ({len(msg)} chars)")
        settings = s.get_settings()
        assert "tts" in settings and "model" in settings
        print(f"  [OK] settings: {list(settings.keys())}")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tool_service():
    print("\n=== Testing Tool Service ===")
    try:
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        prompt = ts.get_tools_prompt()
        assert "shell" in prompt
        print("  [OK] tools prompt")

        test_resp = 'Hello <tool_call type="shell">echo hi</tool_call> done'
        calls = ts.parse_tool_calls(test_resp)
        assert len(calls) == 1 and calls[0]["type"] == "shell"
        print("  [OK] parse tool calls")

        result = ts.run_shell("echo test123")
        assert "test123" in result
        print(f"  [OK] shell exec: {result.strip()}")

        result = ts.list_dir("/tmp")
        assert len(result) > 0
        print("  [OK] list_dir")

        clean = ToolService.strip_tool_tags(test_resp)
        assert "<tool_call" not in clean
        print("  [OK] strip_tool_tags")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_chat_service():
    print("\n=== Testing Chat Service ===")
    try:
        from desktop_app.services.chat_service import ChatService, ANTHROPIC_MODELS
        cs = ChatService()
        assert len(ANTHROPIC_MODELS) >= 10, f"Only {len(ANTHROPIC_MODELS)} models, expected 10+"
        print(f"  [OK] {len(ANTHROPIC_MODELS)} models available")

        # Verify Sonnet 4.6 is default
        assert cs.model_name == "claude-sonnet-4-6"
        print("  [OK] default model: claude-sonnet-4-6")

        # Test model switching
        cs.set_model("claude-opus-4-6")
        assert cs.model_name == "claude-opus-4-6"
        cs.set_model("claude-sonnet-4-6")
        print("  [OK] model switch")

        # Test chat switch
        cs.switch_chat(999)
        print("  [OK] chat switch")

        # Test reload
        cs.reload_config()
        print("  [OK] config reload")

        # Verify NO emergentintegrations
        import inspect
        src = inspect.getsource(ChatService)
        assert "emergentintegrations" not in src, "emergentintegrations still present!"
        assert "anthropic" in src
        print("  [OK] uses anthropic SDK directly (no emergentintegrations)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tts():
    print("\n=== Testing TTS ===")
    try:
        from desktop_app.services.tts_service import TTSService, VOICE_OPTIONS
        tts = TTSService()

        voices = tts.available_voices
        print(f"  [OK] {len(voices)} voices available:")
        for name, model, spk in voices:
            print(f"       - {name} ({model}, speaker={spk})")

        # Check for British male voices
        british_names = [n for n, _, _ in voices if "British" in n or "Jarvis" in n]
        assert len(british_names) >= 2, f"Expected 2+ British voices, got {len(british_names)}"
        print(f"  [OK] {len(british_names)} British male voices")

        # Check Jarvis voice
        jarvis = [n for n, _, _ in voices if "Jarvis" in n]
        assert len(jarvis) == 1, "Jarvis voice missing"
        print(f"  [OK] Jarvis voice: {jarvis[0]}")

        # Toggle
        tts.enabled = True
        assert tts.enabled
        tts.enabled = False
        print("  [OK] toggle")

        # Voice selection
        tts.voice_index = 0
        assert tts.voice_index == 0
        print("  [OK] voice selection")
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
            print("  [SKIP] No voices available")
            return True

        # Test that voice loads without error
        voices = tts.available_voices
        name, model_file, speaker_id = voices[0]
        voice = tts._load_voice(model_file)
        assert voice is not None, f"Failed to load {model_file}"
        print(f"  [OK] Loaded voice: {name}")

        # Synthesize a test phrase to a wav file
        import wave
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()
        with wave.open(tmp_path, "wb") as wf:
            from piper.config import SynthesisConfig
            syn_config = SynthesisConfig(speaker_id=speaker_id)
            voice.synthesize_wav("Testing ONYX text to speech.", wf, syn_config=syn_config)

        size = Path(tmp_path).stat().st_size
        assert size > 1000, f"WAV too small: {size} bytes"
        print(f"  [OK] Synthesized ({size} bytes)")

        Path(tmp_path).unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_ui_components():
    print("\n=== Testing UI Components ===")
    try:
        from desktop_app.ui.styles import MAIN_STYLE, USER_MSG_HTML, AGENT_MSG_HTML, TOOL_MSG_HTML
        assert len(MAIN_STYLE) > 100
        assert "{text}" in USER_MSG_HTML
        assert "{text}" in AGENT_MSG_HTML
        print("  [OK] styles + templates")

        from desktop_app.ui.chat_widget import ChatWidget, ChatThread, VoiceThread, MessageInput
        print("  [OK] chat_widget imports (incl. MessageInput)")

        from desktop_app.ui.main_window import MainWindow
        print("  [OK] main_window imports")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_icon():
    print("\n=== Testing Icon ===")
    svg = Path("install/onyx_icon.svg")
    png = Path("install/onyx_icon.png")
    ok = True
    if svg.exists():
        print(f"  [OK] SVG ({svg.stat().st_size} bytes)")
    else:
        print("  [FAIL] SVG missing")
        ok = False
    if png.exists():
        print(f"  [OK] PNG ({png.stat().st_size} bytes)")
    else:
        print("  [FAIL] PNG missing")
        ok = False
    return ok


def test_directory_structure():
    print("\n=== Testing Directories ===")
    ok = True
    for d in ["Onyx", "Onyx/history", "Onyx/config", "Onyx/voice", "Onyx/logs", "Onyx/voices"]:
        if Path(d).exists():
            print(f"  [OK] {d}")
        else:
            print(f"  [FAIL] {d}")
            ok = False
    return ok


def test_voice_models():
    print("\n=== Testing Voice Models ===")
    voices_dir = Path("Onyx/voices")
    if not voices_dir.exists():
        print("  [FAIL] Onyx/voices directory missing")
        return False
    onnx_files = list(voices_dir.glob("*.onnx"))
    json_files = list(voices_dir.glob("*.onnx.json"))
    print(f"  [OK] {len(onnx_files)} model files, {len(json_files)} config files")
    for f in sorted(onnx_files):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"       - {f.name} ({size_mb:.1f} MB)")
    return len(onnx_files) >= 4


def main():
    print("\n" + "=" * 52)
    print("         ONYX Application Test Suite")
    print("=" * 52)

    tests = [
        ("Imports",          test_imports),
        ("Directories",      test_directory_structure),
        ("Voice Models",     test_voice_models),
        ("Storage",          test_storage),
        ("Config Files",     test_config_files),
        ("Tool Service",     test_tool_service),
        ("Chat Service",     test_chat_service),
        ("TTS",              test_tts),
        ("TTS Synthesis",    test_tts_synthesis),
        ("UI Components",    test_ui_components),
        ("Icon",             test_icon),
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
