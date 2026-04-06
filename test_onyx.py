#!/usr/bin/env python3
"""
ONYX Test Suite
Tests core functionality of the ONYX application
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("\n=== Testing Imports ===")
    
    try:
        import PySide6
        print("✓ PySide6")
    except ImportError as e:
        print(f"✗ PySide6: {e}")
        return False
    
    try:
        import torch
        print("✓ PyTorch")
    except ImportError as e:
        print(f"✗ PyTorch: {e}")
        return False
    
    try:
        import whisper
        print("✓ Whisper")
    except ImportError as e:
        print(f"✗ Whisper: {e}")
        return False
    
    try:
        from emergentintegrations.llm.chat import LlmChat
        print("✓ emergentintegrations")
    except ImportError as e:
        print(f"✗ emergentintegrations: {e}")
        return False
    
    try:
        import pyaudio
        print("✓ PyAudio")
    except ImportError as e:
        print(f"✗ PyAudio: {e}")
        return False
    
    return True

def test_storage():
    """Test storage service initialization"""
    print("\n=== Testing Storage Service ===")
    
    try:
        from desktop_app.services.storage_service import StorageService
        storage = StorageService()
        storage.initialize()
        print("✓ Storage initialized")
        
        # Test database operations
        chat_id = storage.create_chat("Test Chat")
        print(f"✓ Created test chat: {chat_id}")
        
        storage.add_message(chat_id, "user", "Test message")
        storage.add_message(chat_id, "assistant", "Test response")
        print("✓ Added test messages")
        
        messages = storage.get_chat_messages(chat_id)
        assert len(messages) == 2, "Should have 2 messages"
        print(f"✓ Retrieved messages: {len(messages)}")
        
        storage.delete_chat(chat_id)
        print("✓ Deleted test chat")
        
        return True
    except Exception as e:
        print(f"✗ Storage test failed: {e}")
        return False

def test_logger():
    """Test logging system"""
    print("\n=== Testing Logger ===")
    
    try:
        from desktop_app.utils.logger import setup_logger, get_logger
        
        logger = setup_logger()
        logger.info("Test log message")
        print("✓ Logger initialized")
        
        logger2 = get_logger()
        assert logger is logger2, "Should return same logger instance"
        print("✓ Logger singleton working")
        
        return True
    except Exception as e:
        print(f"✗ Logger test failed: {e}")
        return False

def test_personality():
    """Test personality service"""
    print("\n=== Testing Personality Service ===")
    
    try:
        from desktop_app.services.personality_service import PersonalityService
        
        personality = PersonalityService()
        content = personality.get_personality()
        print(f"✓ Loaded personality: {len(content)} characters")
        
        assert "ONYX" in content, "Personality should mention ONYX"
        print("✓ Personality content valid")
        
        return True
    except Exception as e:
        print(f"✗ Personality test failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n=== Testing Environment ===")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("CLAUDE_API_KEY")
    if api_key:
        print(f"✓ CLAUDE_API_KEY configured ({api_key[:10]}...)")
    else:
        print("⚠ CLAUDE_API_KEY not set (required for AI features)")
    
    return True

def test_directory_structure():
    """Test Onyx directory structure"""
    print("\n=== Testing Directory Structure ===")
    
    required_dirs = [
        "Onyx",
        "Onyx/history",
        "Onyx/config",
        "Onyx/voice",
        "Onyx/logs"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} missing")
            all_exist = False
    
    # Check for personality file
    personality_file = Path("Onyx/config/personality.txt")
    if personality_file.exists():
        print(f"✓ personality.txt ({personality_file.stat().st_size} bytes)")
    else:
        print("✗ personality.txt missing")
        all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("       ONYX Application Test Suite")
    print("="*50)
    
    tests = [
        ("Imports", test_imports),
        ("Environment", test_environment),
        ("Directory Structure", test_directory_structure),
        ("Storage Service", test_storage),
        ("Logger", test_logger),
        ("Personality Service", test_personality),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*50)
    print("                  SUMMARY")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ONYX is ready to run.")
        print("\nRun: python3 desktop_app/main.py")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please fix issues before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
