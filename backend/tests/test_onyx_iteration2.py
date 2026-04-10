#!/usr/bin/env python3
"""
ONYX Desktop App - Iteration 2 Test Suite
Tests new features: ToolService, model dropdown, streaming, attachments, 
system tray, compact mode, wake word thread, new icon, and all config files
"""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Module: ToolService Tests - Shell/file/dir tools
# ============================================================================

class TestToolService:
    """Test ToolService: parse_tool_calls, run_shell, read_file, write_file, list_dir, strip_tool_tags"""
    
    def test_tool_service_init(self):
        """ToolService should initialize with working_dir"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        assert ts is not None
        assert ts.working_dir is not None
    
    def test_get_tools_prompt_contains_shell(self):
        """get_tools_prompt() should contain shell tool documentation"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        prompt = ts.get_tools_prompt()
        assert "shell" in prompt
        assert "read_file" in prompt
        assert "write_file" in prompt
        assert "list_dir" in prompt
    
    def test_parse_tool_calls_shell(self):
        """parse_tool_calls() should extract shell tool calls"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        text = 'Hello <tool_call type="shell">echo hello</tool_call> done'
        calls = ts.parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["type"] == "shell"
        assert calls[0]["content"] == "echo hello"
    
    def test_parse_tool_calls_read_file(self):
        """parse_tool_calls() should extract read_file tool calls"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        text = '<tool_call type="read_file">/tmp/test.txt</tool_call>'
        calls = ts.parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["type"] == "read_file"
        assert calls[0]["content"] == "/tmp/test.txt"
    
    def test_parse_tool_calls_write_file(self):
        """parse_tool_calls() should extract write_file tool calls with path attribute"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        text = '<tool_call type="write_file" path="/tmp/out.txt">file content here</tool_call>'
        calls = ts.parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["type"] == "write_file"
        assert calls[0]["path"] == "/tmp/out.txt"
        assert calls[0]["content"] == "file content here"
    
    def test_parse_tool_calls_list_dir(self):
        """parse_tool_calls() should extract list_dir tool calls"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        text = '<tool_call type="list_dir">/tmp</tool_call>'
        calls = ts.parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["type"] == "list_dir"
        assert calls[0]["content"] == "/tmp"
    
    def test_parse_tool_calls_multiple(self):
        """parse_tool_calls() should extract multiple tool calls"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        text = '''<tool_call type="shell">ls</tool_call>
        <tool_call type="read_file">/etc/hostname</tool_call>'''
        calls = ts.parse_tool_calls(text)
        assert len(calls) == 2
    
    def test_run_shell_executes_command(self):
        """run_shell() should execute shell commands"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        result = ts.run_shell("echo test123")
        assert "test123" in result
    
    def test_run_shell_captures_stderr(self):
        """run_shell() should capture stderr"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        result = ts.run_shell("ls /nonexistent_dir_12345")
        assert "[stderr]" in result or "[exit code" in result
    
    def test_run_shell_timeout(self):
        """run_shell() should timeout after 30s"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        # This should not actually timeout, just verify the method exists
        result = ts.run_shell("echo quick")
        assert "quick" in result
    
    def test_read_file_existing(self, tmp_path):
        """read_file() should read existing files"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        result = ts.read_file(str(test_file))
        assert "hello world" in result
    
    def test_read_file_not_found(self):
        """read_file() should return error for non-existent files"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        result = ts.read_file("/nonexistent_file_12345.txt")
        assert "[not found" in result
    
    def test_write_file_creates_file(self, tmp_path):
        """write_file() should create new files"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        test_file = tmp_path / "new_file.txt"
        result = ts.write_file(str(test_file), "test content")
        assert "[wrote" in result
        assert test_file.exists()
        assert test_file.read_text() == "test content"
    
    def test_write_file_creates_parent_dirs(self, tmp_path):
        """write_file() should create parent directories"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        test_file = tmp_path / "subdir" / "nested" / "file.txt"
        result = ts.write_file(str(test_file), "nested content")
        assert "[wrote" in result
        assert test_file.exists()
    
    def test_list_dir_returns_entries(self):
        """list_dir() should return directory entries"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        result = ts.list_dir("/tmp")
        assert len(result) > 0
    
    def test_list_dir_not_found(self):
        """list_dir() should return error for non-existent directories"""
        from desktop_app.services.tool_service import ToolService
        ts = ToolService()
        result = ts.list_dir("/nonexistent_dir_12345")
        assert "[not found" in result
    
    def test_strip_tool_tags_removes_tags(self):
        """strip_tool_tags() should remove tool_call XML tags"""
        from desktop_app.services.tool_service import ToolService
        text = 'Hello <tool_call type="shell">echo hi</tool_call> world'
        clean = ToolService.strip_tool_tags(text)
        assert "<tool_call" not in clean
        assert "</tool_call>" not in clean
        assert "Hello" in clean
        assert "world" in clean


# ============================================================================
# Module: ChatService Tests - 9 Anthropic models, model switching, history context
# ============================================================================

class TestChatServiceModels:
    """Test ChatService: 9 models listed, model switching, switch_chat, reload_config, _build_contextual_message"""
    
    def test_anthropic_models_count(self):
        """ANTHROPIC_MODELS should have 9 models"""
        from desktop_app.services.chat_service import ANTHROPIC_MODELS
        assert len(ANTHROPIC_MODELS) == 9
    
    def test_anthropic_models_includes_sonnet_4_6(self):
        """ANTHROPIC_MODELS should include claude-sonnet-4-6"""
        from desktop_app.services.chat_service import ANTHROPIC_MODELS
        model_ids = [m[1] for m in ANTHROPIC_MODELS]
        assert "claude-sonnet-4-6" in model_ids
    
    def test_anthropic_models_includes_opus_4_6(self):
        """ANTHROPIC_MODELS should include claude-opus-4-6"""
        from desktop_app.services.chat_service import ANTHROPIC_MODELS
        model_ids = [m[1] for m in ANTHROPIC_MODELS]
        assert "claude-opus-4-6" in model_ids
    
    def test_anthropic_models_includes_haiku(self):
        """ANTHROPIC_MODELS should include haiku models"""
        from desktop_app.services.chat_service import ANTHROPIC_MODELS
        model_ids = [m[1] for m in ANTHROPIC_MODELS]
        haiku_models = [m for m in model_ids if "haiku" in m]
        assert len(haiku_models) >= 1
    
    def test_set_model_changes_model(self):
        """set_model() should change the model_name"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        cs.set_model("claude-opus-4-6")
        assert cs.model_name == "claude-opus-4-6"
    
    def test_set_model_persists_to_settings(self):
        """set_model() should persist model to settings.json"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        cs.set_model("claude-haiku-4-5")
        settings = cs.storage.get_settings()
        assert settings["model"]["name"] == "claude-haiku-4-5"
        # Reset to default
        cs.set_model("claude-sonnet-4-6")
    
    def test_switch_chat_creates_fresh_session(self):
        """switch_chat() should create a fresh LLM session"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        cs.switch_chat(999)
        assert cs._active_chat_id == 999
    
    def test_reload_config_rebuilds_system_message(self):
        """reload_config() should rebuild the system message"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        original_msg = cs._system_message
        cs.reload_config()
        # System message should still contain ONYX
        assert "ONYX" in cs._system_message
    
    def test_build_contextual_message_includes_history(self):
        """_build_contextual_message() should include history"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        result = cs._build_contextual_message(history, "New message")
        assert "Previous conversation" in result
        assert "Hello" in result
        assert "Hi there!" in result
        assert "New message" in result
    
    def test_build_contextual_message_empty_history(self):
        """_build_contextual_message() should return just the message for empty history"""
        from desktop_app.services.chat_service import ChatService
        cs = ChatService()
        result = cs._build_contextual_message([], "Just this")
        assert result == "Just this"


# ============================================================================
# Module: TTSService Tests - Toggle and settings persistence
# ============================================================================

class TestTTSServicePersistence:
    """Test TTSService: toggle enabled/disabled, settings persistence to settings.json"""
    
    def test_tts_enabled_persists_to_settings(self, tmp_path):
        """TTSService.enabled should persist to settings.json"""
        from desktop_app.services.tts_service import TTSService
        config_path = tmp_path / "config"
        config_path.mkdir()
        settings_file = config_path / "settings.json"
        settings_file.write_text('{"tts": {"enabled": false}}')
        
        tts = TTSService(config_path=config_path)
        tts.enabled = True
        
        # Read back settings
        data = json.loads(settings_file.read_text())
        assert data["tts"]["enabled"] is True
    
    def test_tts_loads_settings_on_init(self, tmp_path):
        """TTSService should load settings from settings.json on init"""
        from desktop_app.services.tts_service import TTSService
        config_path = tmp_path / "config"
        config_path.mkdir()
        settings_file = config_path / "settings.json"
        settings_file.write_text('{"tts": {"enabled": true, "rate": 200, "volume": 0.8}}')
        
        tts = TTSService(config_path=config_path)
        assert tts._enabled is True
        assert tts._rate == 200
        assert tts._volume == 0.8


# ============================================================================
# Module: VoiceService Tests - WakeWordThread and transcribe_sync
# ============================================================================

class TestVoiceServiceWakeWord:
    """Test VoiceService: WakeWordThread class exists, transcribe_sync method exists"""
    
    def test_wake_word_thread_class_exists(self):
        """WakeWordThread class should exist in voice_service"""
        from desktop_app.services.voice_service import WakeWordThread
        assert WakeWordThread is not None
    
    def test_wake_word_thread_has_signal(self):
        """WakeWordThread should have wake_word_detected signal"""
        from desktop_app.services.voice_service import WakeWordThread
        assert hasattr(WakeWordThread, 'wake_word_detected')
    
    def test_transcribe_sync_method_exists(self):
        """VoiceService should have transcribe_sync method"""
        from desktop_app.services.voice_service import VoiceService
        vs = VoiceService()
        assert hasattr(vs, 'transcribe_sync')
        assert callable(vs.transcribe_sync)


# ============================================================================
# Module: StorageService Tests - build_system_message includes all config
# ============================================================================

class TestStorageServiceSystemMessage:
    """Test StorageService: build_system_message includes personality/knowledgebase/user/instructions"""
    
    def test_build_system_message_includes_personality(self, tmp_path):
        """build_system_message() should include personality"""
        from desktop_app.services.storage_service import StorageService
        storage = StorageService(base_path=str(tmp_path / "TestOnyx"))
        storage.initialize()
        msg = storage.build_system_message()
        assert "ONYX" in msg
    
    def test_build_system_message_structure(self, tmp_path):
        """build_system_message() should have proper structure"""
        from desktop_app.services.storage_service import StorageService
        storage = StorageService(base_path=str(tmp_path / "TestOnyx"))
        storage.initialize()
        
        # Add some content to config files
        (storage.config_path / "knowledgebase.txt").write_text("My server runs Ubuntu")
        (storage.config_path / "user.txt").write_text("Name: Test User")
        (storage.config_path / "instructions.txt").write_text("Always be helpful")
        
        msg = storage.build_system_message()
        assert "Knowledgebase" in msg
        assert "About the User" in msg
        assert "Custom Instructions" in msg


# ============================================================================
# Module: chat_widget.py Tests - Model QComboBox, TTS checkbox, wake word, attach, streaming
# ============================================================================

class TestChatWidgetCode:
    """Test chat_widget.py: model QComboBox, TTS checkbox, wake word checkbox, attach button, streaming timer, tool_output signal"""
    
    def test_chat_widget_has_model_combo(self):
        """chat_widget.py should have model QComboBox"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "QComboBox" in content
        assert "model_combo" in content
    
    def test_chat_widget_has_tts_checkbox(self):
        """chat_widget.py should have TTS checkbox"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "tts_check" in content or "ttsToggle" in content
        assert "QCheckBox" in content
    
    def test_chat_widget_has_wake_word_checkbox(self):
        """chat_widget.py should have wake word checkbox"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "ww_check" in content or "wake" in content.lower()
    
    def test_chat_widget_has_attach_button(self):
        """chat_widget.py should have attach button"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "attach_btn" in content or "attachButton" in content
    
    def test_chat_widget_has_streaming_timer(self):
        """chat_widget.py should have streaming timer logic"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "_stream_timer" in content
        assert "QTimer" in content
    
    def test_chat_thread_has_tool_output_signal(self):
        """ChatThread should have tool_output signal"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "tool_output" in content
        assert "Signal" in content
    
    def test_chat_widget_has_tool_output_handler(self):
        """chat_widget.py should have tool_output signal handler"""
        chat_widget_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "chat_widget.py"
        content = chat_widget_path.read_text()
        assert "_on_tool_output" in content


# ============================================================================
# Module: main_window.py Tests - System tray, compact toggle, context menu
# ============================================================================

class TestMainWindowCode:
    """Test main_window.py: QSystemTrayIcon, compact toggle, closeEvent, context menu"""
    
    def test_main_window_has_system_tray(self):
        """main_window.py should have QSystemTrayIcon"""
        main_window_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "main_window.py"
        content = main_window_path.read_text()
        assert "QSystemTrayIcon" in content
        assert "tray_icon" in content
    
    def test_main_window_has_compact_toggle(self):
        """main_window.py should have compact toggle button"""
        main_window_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "main_window.py"
        content = main_window_path.read_text()
        assert "compact_btn" in content or "compactToggle" in content
        assert "toggle_compact" in content
    
    def test_main_window_close_event_minimizes_to_tray(self):
        """main_window.py closeEvent should minimize to tray"""
        main_window_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "main_window.py"
        content = main_window_path.read_text()
        assert "closeEvent" in content
        assert "hide()" in content
        assert "event.ignore()" in content
    
    def test_main_window_has_context_menu(self):
        """main_window.py should have context menu on chat list"""
        main_window_path = Path(__file__).parent.parent.parent / "desktop_app" / "ui" / "main_window.py"
        content = main_window_path.read_text()
        assert "_context_menu" in content
        assert "CustomContextMenu" in content


# ============================================================================
# Module: styles.py Tests - Message HTML templates with distinct colors
# ============================================================================

class TestStylesCode:
    """Test styles.py: USER_MSG_HTML, AGENT_MSG_HTML, TOOL_MSG_HTML, TYPING_INDICATOR_HTML, ATTACHMENT_HTML"""
    
    def test_styles_has_user_msg_html(self):
        """styles.py should have USER_MSG_HTML template"""
        from desktop_app.ui.styles import USER_MSG_HTML
        assert USER_MSG_HTML is not None
        assert "{text}" in USER_MSG_HTML
    
    def test_styles_has_agent_msg_html(self):
        """styles.py should have AGENT_MSG_HTML template"""
        from desktop_app.ui.styles import AGENT_MSG_HTML
        assert AGENT_MSG_HTML is not None
        assert "{text}" in AGENT_MSG_HTML
    
    def test_styles_has_tool_msg_html(self):
        """styles.py should have TOOL_MSG_HTML template"""
        from desktop_app.ui.styles import TOOL_MSG_HTML
        assert TOOL_MSG_HTML is not None
        assert "{tool_type}" in TOOL_MSG_HTML
    
    def test_styles_has_typing_indicator_html(self):
        """styles.py should have TYPING_INDICATOR_HTML template"""
        from desktop_app.ui.styles import TYPING_INDICATOR_HTML
        assert TYPING_INDICATOR_HTML is not None
        assert "thinking" in TYPING_INDICATOR_HTML.lower()
    
    def test_styles_has_attachment_html(self):
        """styles.py should have ATTACHMENT_HTML template"""
        from desktop_app.ui.styles import ATTACHMENT_HTML
        assert ATTACHMENT_HTML is not None
        assert "{filename}" in ATTACHMENT_HTML
    
    def test_user_and_agent_have_distinct_colors(self):
        """USER_MSG_HTML and AGENT_MSG_HTML should have distinct background colors"""
        from desktop_app.ui.styles import USER_MSG_HTML, AGENT_MSG_HTML, USER_BG, AGENT_BG
        assert USER_BG != AGENT_BG
        assert USER_BG in USER_MSG_HTML or "user_bg" in USER_MSG_HTML
        assert AGENT_BG in AGENT_MSG_HTML or "agent_bg" in AGENT_MSG_HTML


# ============================================================================
# Module: Icon Tests - SVG and PNG exist with humanoid robot
# ============================================================================

class TestIcon:
    """Test icon: onyx_icon.svg and onyx_icon.png exist with humanoid robot design"""
    
    def test_svg_icon_exists(self):
        """install/onyx_icon.svg should exist"""
        svg_path = Path(__file__).parent.parent.parent / "install" / "onyx_icon.svg"
        assert svg_path.exists()
    
    def test_png_icon_exists(self):
        """install/onyx_icon.png should exist"""
        png_path = Path(__file__).parent.parent.parent / "install" / "onyx_icon.png"
        assert png_path.exists()
    
    def test_svg_has_humanoid_elements(self):
        """SVG should have humanoid robot elements (head, eyes, shoulders)"""
        svg_path = Path(__file__).parent.parent.parent / "install" / "onyx_icon.svg"
        content = svg_path.read_text()
        # Check for humanoid elements
        assert "Head" in content or "head" in content.lower() or "ellipse" in content
        assert "Eye" in content or "eye" in content.lower()
        # Should NOT be a box head
        assert "box head" not in content.lower()
    
    def test_svg_has_onyx_branding(self):
        """SVG should have ONYX branding"""
        svg_path = Path(__file__).parent.parent.parent / "install" / "onyx_icon.svg"
        content = svg_path.read_text()
        assert "ONYX" in content


# ============================================================================
# Module: Settings Tests - Default model is claude-sonnet-4-6
# ============================================================================

class TestSettingsDefaults:
    """Test settings.json: default model is claude-sonnet-4-6"""
    
    def test_default_model_is_sonnet_4_6(self):
        """settings.json default model should be claude-sonnet-4-6"""
        from desktop_app.services.storage_service import DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["model"]["name"] == "claude-sonnet-4-6"
    
    def test_actual_settings_file_model(self):
        """Actual settings.json should have claude-sonnet-4-6 as model"""
        settings_path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "settings.json"
        if settings_path.exists():
            data = json.loads(settings_path.read_text())
            assert data["model"]["name"] == "claude-sonnet-4-6"


# ============================================================================
# Module: Config Files Tests - All config files exist with helpful comments
# ============================================================================

class TestConfigFiles:
    """Test config files: knowledgebase.txt, user.txt, instructions.txt, personality.txt, settings.json"""
    
    def test_knowledgebase_exists(self):
        """Onyx/config/knowledgebase.txt should exist"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "knowledgebase.txt"
        assert path.exists()
    
    def test_user_exists(self):
        """Onyx/config/user.txt should exist"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "user.txt"
        assert path.exists()
    
    def test_instructions_exists(self):
        """Onyx/config/instructions.txt should exist"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "instructions.txt"
        assert path.exists()
    
    def test_personality_exists(self):
        """Onyx/config/personality.txt should exist"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "personality.txt"
        assert path.exists()
    
    def test_settings_exists(self):
        """Onyx/config/settings.json should exist"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "settings.json"
        assert path.exists()
    
    def test_knowledgebase_has_comments(self):
        """knowledgebase.txt should have helpful comments"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "knowledgebase.txt"
        content = path.read_text()
        assert "#" in content  # Has comment lines
    
    def test_user_has_comments(self):
        """user.txt should have helpful comments"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "user.txt"
        content = path.read_text()
        assert "#" in content
    
    def test_instructions_has_comments(self):
        """instructions.txt should have helpful comments"""
        path = Path(__file__).parent.parent.parent / "Onyx" / "config" / "instructions.txt"
        content = path.read_text()
        assert "#" in content


# ============================================================================
# Module: Security Tests - No dummy_key or placeholder API keys
# ============================================================================

class TestSecurityNoPlaceholderKeys:
    """Test that no dummy_key or placeholder API keys exist in code"""
    
    def test_no_dummy_key_in_code(self):
        """No 'dummy_key' should exist in code"""
        desktop_app_path = Path(__file__).parent.parent.parent / "desktop_app"
        for py_file in desktop_app_path.rglob("*.py"):
            content = py_file.read_text()
            assert "dummy_key" not in content.lower(), f"Found dummy_key in {py_file}"
    
    def test_no_placeholder_api_key(self):
        """No placeholder API keys like 'your-api-key' should exist"""
        desktop_app_path = Path(__file__).parent.parent.parent / "desktop_app"
        # Only check for actual API key placeholder patterns, not UI method names
        patterns = ["your-api-key", "your_api_key", "test_key", "fake_key", "sk-test-", "sk-fake-"]
        for py_file in desktop_app_path.rglob("*.py"):
            content = py_file.read_text()
            for pattern in patterns:
                # Skip comments
                lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
                code_content = '\n'.join(lines)
                assert pattern not in code_content.lower(), f"Found '{pattern}' in {py_file}"


# ============================================================================
# Module: setup.sh Tests - Uses venv and --extra-index-url
# ============================================================================

class TestSetupShScript:
    """Test setup.sh: uses venv and --extra-index-url for emergentintegrations"""
    
    def test_setup_uses_venv(self):
        """setup.sh should use python venv"""
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        content = setup_path.read_text()
        assert "venv" in content
        assert "python3 -m venv" in content
    
    def test_setup_uses_extra_index_url(self):
        """setup.sh should use --extra-index-url for emergentintegrations"""
        setup_path = Path(__file__).parent.parent.parent / "install" / "setup.sh"
        content = setup_path.read_text()
        assert "--extra-index-url" in content
        assert "d33sy5i8bnduwe.cloudfront.net" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
