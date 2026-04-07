#!/usr/bin/env python3
"""ONYX Test Suite — validates core modules and services"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all required modules can be imported"""
    print("\n=== Testing Imports ===")
    ok = True

    for name, stmt in [
        ("PySide6",              "import PySide6"),
        ("emergentintegrations", "from emergentintegrations.llm.chat import LlmChat, UserMessage"),
        ("pyttsx3",              "import pyttsx3"),
        ("dotenv",               "from dotenv import load_dotenv"),
    ]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError as e:
            print(f"  [FAIL] {name}: {e}")
            ok = False

    # Optional heavy deps
    for name, stmt in [
        ("torch",   "import torch"),
        ("whisper", "import whisper"),
        ("pyaudio", "import pyaudio"),
    ]:
        try:
            exec(stmt)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [WARN] {name} not installed (voice features disabled)")

    return ok


def test_storage():
    """Test storage service"""
    print("\n=== Testing Storage Service ===")
    try:
        from desktop_app.services.storage_service import StorageService
        storage = StorageService()
        storage.initialize()
        print("  [OK] Storage initialized")

        chat_id = storage.create_chat("Test Chat")
        print(f"  [OK] Created chat {chat_id}")

        storage.add_message(chat_id, "user", "hello")
        storage.add_message(chat_id, "assistant", "hi there")
        msgs = storage.get_chat_messages(chat_id)
        assert len(msgs) == 2
        print(f"  [OK] Messages: {len(msgs)}")

        storage.delete_chat(chat_id)
        print("  [OK] Deleted test chat")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_logger():
    """Test logging"""
    print("\n=== Testing Logger ===")
    try:
        from desktop_app.utils.logger import setup_logger, get_logger
        logger = setup_logger()
        logger.info("test log entry")
        print("  [OK] Logger works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_personality():
    """Test personality service"""
    print("\n=== Testing Personality ===")
    try:
        from desktop_app.services.personality_service import PersonalityService
        ps = PersonalityService()
        content = ps.get_personality()
        assert "ONYX" in content
        print(f"  [OK] Personality loaded ({len(content)} chars)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_tts():
    """Test TTS service"""
    print("\n=== Testing TTS Service ===")
    try:
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        print(f"  [OK] TTS available: {tts.available}")
        print(f"  [OK] TTS enabled (default): {tts.enabled}")
        tts.enabled = True
        assert tts.enabled is True
        tts.enabled = False
        print("  [OK] Toggle works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_config_files():
    """Test knowledgebase, user profile, instructions, and settings"""
    print("\n=== Testing Config Files ===")
    try:
        from desktop_app.services.storage_service import StorageService
        s = StorageService()
        s.initialize()

        # Check files exist
        for f in ["knowledgebase.txt", "user.txt", "instructions.txt", "settings.json"]:
            assert (s.config_path / f).exists(), f"{f} missing"
            print(f"  [OK] {f} exists")

        # Comment-only files return empty string (no content injected)
        kb = s.get_knowledgebase()
        assert isinstance(kb, str)
        print(f"  [OK] knowledgebase: {len(kb)} chars (stripped)")

        up = s.get_user_profile()
        assert isinstance(up, str)
        print(f"  [OK] user profile: {len(up)} chars (stripped)")

        instr = s.get_instructions()
        assert isinstance(instr, str)
        print(f"  [OK] instructions: {len(instr)} chars (stripped)")

        # Settings round-trip
        settings = s.get_settings()
        assert "tts" in settings
        assert "model" in settings
        print(f"  [OK] settings loaded: {list(settings.keys())}")

        # System message assembly
        msg = s.build_system_message()
        assert "ONYX" in msg
        print(f"  [OK] system message: {len(msg)} chars")

        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_chat_service():
    """Test chat service initialisation (no API call)"""
    print("\n=== Testing Chat Service ===")
    try:
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        print(f"  [OK] Chat service init (model: Claude Opus 4.6)")

        # Test reload_config
        cs.reload_config()
        print(f"  [OK] Config reload works")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_directory_structure():
    """Test Onyx directories"""
    print("\n=== Testing Directory Structure ===")
    ok = True
    for d in ["Onyx", "Onyx/history", "Onyx/config", "Onyx/voice", "Onyx/logs"]:
        if Path(d).exists():
            print(f"  [OK] {d}")
        else:
            print(f"  [FAIL] {d} missing")
            ok = False

    pf = Path("Onyx/config/personality.txt")
    if pf.exists():
        print(f"  [OK] personality.txt ({pf.stat().st_size} bytes)")
    else:
        print("  [FAIL] personality.txt missing")
        ok = False
    return ok


def main():
    print("\n" + "=" * 50)
    print("        ONYX Application Test Suite")
    print("=" * 50)

    tests = [
        ("Imports",          test_imports),
        ("Directory Layout", test_directory_structure),
        ("Storage Service",  test_storage),
        ("Logger",           test_logger),
        ("Personality",      test_personality),
        ("TTS Service",      test_tts),
        ("Config Files",     test_config_files),
        ("Chat Service",     test_chat_service),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [CRASH] {name}: {e}")
            results[name] = False

    print("\n" + "=" * 50)
    print("                 SUMMARY")
    print("=" * 50)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
