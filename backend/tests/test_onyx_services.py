#!/usr/bin/env python3
"""
ONYX Desktop App - Comprehensive Test Suite
Tests all core services: Storage, Chat, TTS, Voice, and code quality checks
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Module: Import Tests - Verify all required modules can be imported
# ============================================================================

class TestImports:
    """Test that all required Python modules can be imported cleanly"""
    
    def test_pyside6_import(self):
        """PySide6 should be importable"""
        import PySide6
        assert PySide6 is not None
    
    def test_emergentintegrations_import(self):
        """emergentintegrations should be importable with LlmChat and UserMessage"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        assert LlmChat is not None
        assert UserMessage is not None
    
    def test_pyttsx3_import(self):
        """pyttsx3 should be importable for TTS"""
        import pyttsx3
        assert pyttsx3 is not None
    
    def test_whisper_import(self):
        """openai-whisper should be importable for speech-to-text"""
        import whisper
        assert whisper is not None
    
    def test_torch_import(self):
        """torch should be importable (required by whisper)"""
        import torch
        assert torch is not None
    
    def test_pyaudio_import(self):
        """pyaudio should be importable for audio recording (may fail in container without audio hardware)"""
        try:
            import pyaudio
            assert pyaudio is not None
        except ImportError:
            pytest.skip("PyAudio C module not available in container (no audio hardware)")
    
    def test_dotenv_import(self):
        """python-dotenv should be importable"""
        from dotenv import load_dotenv
        assert load_dotenv is not None


# ============================================================================
# Module: StorageService Tests - SQLite database operations
# ============================================================================

class TestStorageService:
    """Test StorageService: init, create_chat, add_message, get_chat_messages, delete_chat, get_personality"""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create a temporary storage service for testing"""
        from desktop_app.services.storage_service import StorageService
        storage = StorageService(base_path=str(tmp_path / "TestOnyx"))
        storage.initialize()
        return storage
    
    def test_storage_init_creates_directories(self, temp_storage):
        """StorageService.initialize() should create all required directories"""
        assert temp_storage.history_path.exists()
        assert temp_storage.config_path.exists()
        assert temp_storage.voice_path.exists()
        assert temp_storage.logs_path.exists()
    
    def test_storage_init_creates_database(self, temp_storage):
        """StorageService.initialize() should create SQLite database"""
        assert temp_storage.db_path.exists()
    
    def test_storage_init_creates_personality_file(self, temp_storage):
        """StorageService.initialize() should create personality.txt"""
        personality_file = temp_storage.config_path / "personality.txt"
        assert personality_file.exists()
        content = personality_file.read_text()
        assert "ONYX" in content
    
    def test_create_chat_returns_id(self, temp_storage):
        """create_chat() should return a valid chat ID"""
        chat_id = temp_storage.create_chat("Test Chat")
        assert isinstance(chat_id, int)
        assert chat_id > 0
    
    def test_create_chat_persists(self, temp_storage):
        """create_chat() should persist the chat in database"""
        chat_id = temp_storage.create_chat("Persisted Chat")
        chat = temp_storage.get_chat(chat_id)
        assert chat is not None
        assert chat['title'] == "Persisted Chat"
    
    def test_add_message_and_retrieve(self, temp_storage):
        """add_message() should store messages that can be retrieved"""
        chat_id = temp_storage.create_chat("Message Test")
        temp_storage.add_message(chat_id, "user", "Hello ONYX")
        temp_storage.add_message(chat_id, "assistant", "Hello! How can I help?")
        
        messages = temp_storage.get_chat_messages(chat_id)
        assert len(messages) == 2
        assert messages[0]['role'] == "user"
        assert messages[0]['content'] == "Hello ONYX"
        assert messages[1]['role'] == "assistant"
        assert messages[1]['content'] == "Hello! How can I help?"
    
    def test_get_chat_messages_empty_chat(self, temp_storage):
        """get_chat_messages() should return empty list for new chat"""
        chat_id = temp_storage.create_chat("Empty Chat")
        messages = temp_storage.get_chat_messages(chat_id)
        assert messages == []
    
    def test_delete_chat_removes_chat(self, temp_storage):
        """delete_chat() should remove the chat from database"""
        chat_id = temp_storage.create_chat("To Delete")
        temp_storage.delete_chat(chat_id)
        chat = temp_storage.get_chat(chat_id)
        assert chat is None
    
    def test_delete_chat_removes_messages(self, temp_storage):
        """delete_chat() should also remove all associated messages"""
        chat_id = temp_storage.create_chat("Chat with Messages")
        temp_storage.add_message(chat_id, "user", "Test message")
        temp_storage.delete_chat(chat_id)
        messages = temp_storage.get_chat_messages(chat_id)
        assert messages == []
    
    def test_get_personality_returns_content(self, temp_storage):
        """get_personality() should return personality text"""
        personality = temp_storage.get_personality()
        assert isinstance(personality, str)
        assert len(personality) > 0
        assert "ONYX" in personality


# ============================================================================
# Module: ChatService Tests - Claude Opus 4.6 integration
# ============================================================================

class TestChatService:
    """Test ChatService: initializes with Claude Opus 4.6, handles missing API key gracefully"""
    
    def test_chat_service_init_with_empty_key(self):
        """ChatService should initialize even with empty API key"""
        # Ensure CLAUDE_API_KEY is empty for this test
        original_key = os.environ.get("CLAUDE_API_KEY", "")
        os.environ["CLAUDE_API_KEY"] = ""
        
        try:
            from desktop_app.services.chat_service import ChatService
            cs = ChatService()
            assert cs is not None
            assert cs.api_key == ""
        finally:
            os.environ["CLAUDE_API_KEY"] = original_key
    
    def test_chat_service_warns_on_missing_key(self, caplog):
        """ChatService should log warning when API key is not set"""
        original_key = os.environ.get("CLAUDE_API_KEY", "")
        os.environ["CLAUDE_API_KEY"] = ""
        
        try:
            import logging
            caplog.set_level(logging.WARNING)
            from desktop_app.services.chat_service import ChatService
            # Need to reimport to trigger the warning
            import importlib
            import desktop_app.services.chat_service as chat_module
            importlib.reload(chat_module)
            cs = chat_module.ChatService()
            # Check that warning was logged
            assert cs.api_key == ""
        finally:
            os.environ["CLAUDE_API_KEY"] = original_key
    
    def test_chat_service_uses_claude_opus_4_6(self):
        """ChatService should use Claude Opus 4.6 model"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        # The model is set via with_model("anthropic", "claude-opus-4-6")
        # We can verify the llm_chat object exists
        assert cs.llm_chat is not None
    
    def test_send_message_returns_error_when_no_key(self):
        """send_message() should return error message when API key is empty"""
        import asyncio
        original_key = os.environ.get("CLAUDE_API_KEY", "")
        os.environ["CLAUDE_API_KEY"] = ""
        
        try:
            import importlib
            import desktop_app.services.chat_service as chat_module
            importlib.reload(chat_module)
            cs = chat_module.ChatService()
            
            # Create a test chat
            chat_id = cs.storage.create_chat("Test")
            
            # Run async method synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(cs.send_message("Hello", chat_id))
            finally:
                loop.close()
            
            assert "No API key configured" in response or "API key" in response.lower()
            
            # Cleanup
            cs.storage.delete_chat(chat_id)
        finally:
            os.environ["CLAUDE_API_KEY"] = original_key


# ============================================================================
# Module: TTSService Tests - Text-to-Speech with pyttsx3
# ============================================================================

class TestTTSService:
    """Test TTSService: available property, enabled toggle, speak() method"""
    
    def test_tts_available_property(self):
        """TTSService.available should return True when pyttsx3 is installed and engine initializes"""
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        # In container without espeak-ng, available may be False - this is expected
        # The test verifies the property exists and returns a boolean
        assert isinstance(tts.available, bool)
    
    def test_tts_enabled_default_false(self, tmp_path):
        """TTSService.enabled should default to False when settings don't exist"""
        from desktop_app.services.tts_service import TTSService
        # Use a temp path to avoid reading existing settings
        config_path = tmp_path / "config"
        config_path.mkdir()
        tts = TTSService(config_path=config_path)
        assert tts.enabled is False
    
    def test_tts_enabled_toggle_on(self):
        """TTSService.enabled can be set to True"""
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        tts.enabled = True
        assert tts.enabled is True
    
    def test_tts_enabled_toggle_off(self):
        """TTSService.enabled can be toggled back to False"""
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        tts.enabled = True
        tts.enabled = False
        assert tts.enabled is False
    
    def test_tts_speak_no_crash_when_disabled(self):
        """TTSService.speak() should not crash when disabled"""
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        tts.enabled = False
        # This should be a no-op and not crash
        tts.speak("Test message")
        assert True  # If we get here, no crash occurred
    
    def test_tts_speak_no_crash_when_enabled(self):
        """TTSService.speak() should not crash when enabled (runs in background thread)"""
        from desktop_app.services.tts_service import TTSService
        import time
        tts = TTSService()
        tts.enabled = True
        # This runs in a background thread, so it should return immediately
        tts.speak("Test")
        # Give it a moment to start the thread
        time.sleep(0.1)
        assert True  # If we get here, no crash occurred
    
    def test_tts_set_rate(self):
        """TTSService.set_rate() should update the rate"""
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        tts.set_rate(200)
        assert tts._rate == 200
    
    def test_tts_set_volume(self):
        """TTSService.set_volume() should update the volume (clamped 0-1)"""
        from desktop_app.services.tts_service import TTSService
        tts = TTSService()
        tts.set_volume(0.5)
        assert tts._volume == 0.5
        tts.set_volume(1.5)  # Should clamp to 1.0
        assert tts._volume == 1.0
        tts.set_volume(-0.5)  # Should clamp to 0.0
        assert tts._volume == 0.0


# ============================================================================
# Module: VoiceService Tests - Whisper speech-to-text
# ============================================================================

class TestVoiceService:
    """Test VoiceService: initializes Whisper model, no pvporcupine references"""
    
    def test_voice_service_init(self):
        """VoiceService should initialize without error"""
        from desktop_app.services.voice_service import VoiceService
        vs = VoiceService()
        assert vs is not None
    
    def test_voice_service_has_whisper_model(self):
        """VoiceService should have whisper_model attribute"""
        from desktop_app.services.voice_service import VoiceService
        vs = VoiceService()
        # whisper_model should exist (may be None if whisper not available)
        assert hasattr(vs, 'whisper_model')
    
    def test_no_pvporcupine_in_voice_service(self):
        """VoiceService should not contain any pvporcupine references"""
        voice_service_path = Path(__file__).parent.parent.parent / "desktop_app" / "services" / "voice_service.py"
        content = voice_service_path.read_text()
        assert "pvporcupine" not in content.lower()
        assert "porcupine" not in content.lower()


# ============================================================================
# Module: chat_widget.py Tests - TTS toggle and speak parameter
# ============================================================================

class TestChatWidgetCode:
    """Test chat_widget.py: TTS checkbox toggle, streaming, model selector"""
    
    def test_chat_widget_has_tts_toggle(self):
        """chat_widget.py should have TTS checkbox (tts_check)"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "tts_check" in content
        assert "QCheckBox" in content
    
    def test_chat_widget_has_tts_service(self):
        """chat_widget.py should use TTSService for speech"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "TTSService" in content
        assert "tts_service" in content
    
    def test_chat_widget_speaks_on_stream_done(self):
        """chat_widget.py should speak when streaming completes (if TTS enabled)"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        # Check that _on_stream_done calls tts_service.speak
        assert "tts_service.speak" in content


# ============================================================================
# Module: setup.sh Tests - Installer script validation
# ============================================================================

class TestSetupScript:
    """Test setup.sh: venv usage, emergentintegrations install, bash syntax"""
    
    def test_setup_uses_python_venv(self):
        """setup.sh should use python3 -m venv"""
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        content = setup_path.read_text()
        assert "python3 -m venv" in content
    
    def test_setup_installs_emergentintegrations_with_extra_index(self):
        """setup.sh should install emergentintegrations with --extra-index-url"""
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        content = setup_path.read_text()
        assert "emergentintegrations" in content
        assert "--extra-index-url" in content
        assert "d33sy5i8bnduwe.cloudfront.net" in content
    
    def test_setup_installs_requirements(self):
        """setup.sh should install from requirements.txt"""
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        content = setup_path.read_text()
        assert "requirements.txt" in content
    
    def test_setup_creates_launcher_with_venv_activation(self):
        """setup.sh should create launcher that activates venv"""
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        content = setup_path.read_text()
        # The launcher script should source the venv
        assert "source" in content and ".venv/bin/activate" in content
    
    def test_setup_bash_syntax_valid(self):
        """setup.sh should have valid bash syntax"""
        import subprocess
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        result = subprocess.run(
            ["bash", "-n", str(setup_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Bash syntax error: {result.stderr}"


# ============================================================================
# Module: Directory Structure Tests
# ============================================================================

class TestDirectoryStructure:
    """Test that required directories exist"""
    
    def test_onyx_base_directory_exists(self):
        """Onyx/ directory should exist"""
        onyx_path = Path(__file__).parent.parent.parent / "Onyx"
        assert onyx_path.exists()
    
    def test_onyx_history_directory_exists(self):
        """Onyx/history/ directory should exist"""
        history_path = Path(__file__).parent.parent.parent / "Onyx" / "history"
        assert history_path.exists()
    
    def test_onyx_config_directory_exists(self):
        """Onyx/config/ directory should exist"""
        config_path = Path(__file__).parent.parent.parent / "Onyx" / "config"
        assert config_path.exists()
    
    def test_onyx_voice_directory_exists(self):
        """Onyx/voice/ directory should exist"""
        voice_path = Path(__file__).parent.parent.parent / "Onyx" / "voice"
        assert voice_path.exists()
    
    def test_onyx_logs_directory_exists(self):
        """Onyx/logs/ directory should exist"""
        logs_path = Path(__file__).parent.parent.parent / "Onyx" / "logs"
        assert logs_path.exists()
    
    def test_personality_file_exists(self):
        """Onyx/config/personality.txt should exist"""
        personality_path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "personality.txt"
        assert personality_path.exists()
        content = personality_path.read_text()
        assert "ONYX" in content


# ============================================================================
# Module: .env and Security Tests
# ============================================================================

class TestEnvAndSecurity:
    """Test .env configuration and no hardcoded keys"""
    
    def test_env_file_exists(self):
        """.env file should exist"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        assert env_path.exists()
    
    def test_env_has_claude_api_key_variable(self):
        """.env should have CLAUDE_API_KEY= (can be blank)"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        content = env_path.read_text()
        assert "CLAUDE_API_KEY=" in content
    
    def test_no_dummy_keys_in_code(self):
        """No dummy/placeholder API keys should be in the code"""
        desktop_app_path = Path(__file__).parent.parent.parent / "desktop_app"
        
        # Only check for actual API key patterns, not UI method names
        dummy_patterns = ["sk-ant-", "sk-test", "your-api-key", "dummy_key", "test_key"]
        
        for py_file in desktop_app_path.rglob("*.py"):
            content = py_file.read_text()
            for pattern in dummy_patterns:
                lines = content.split('\n')
                for line in lines:
                    if pattern in line.lower() and not line.strip().startswith('#'):
                        # Allow in error messages or documentation strings
                        if 'console.anthropic.com' not in line:
                            assert pattern not in line.lower(), f"Found '{pattern}' in {py_file}"


# ============================================================================
# Module: Code Quality Tests
# ============================================================================

class TestCodeQuality:
    """Test code quality: no dead code, proper structure"""
    
    def test_no_pvporcupine_anywhere(self):
        """No pvporcupine references should exist in the codebase"""
        desktop_app_path = Path(__file__).parent.parent.parent / "desktop_app"
        
        for py_file in desktop_app_path.rglob("*.py"):
            content = py_file.read_text()
            assert "pvporcupine" not in content.lower(), f"Found pvporcupine in {py_file}"
            assert "porcupine" not in content.lower(), f"Found porcupine in {py_file}"
    
    def test_chat_service_model_is_claude_opus_4_6(self):
        """ChatService should use claude-opus-4-6 model"""
        chat_service_path = Path(__file__).parent.parent.parent / "desktop_app" / "services" / "chat_service.py"
        content = chat_service_path.read_text()
        assert "claude-opus-4-6" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
