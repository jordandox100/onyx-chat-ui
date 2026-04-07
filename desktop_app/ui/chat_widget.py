"""Chat widget for displaying and managing conversations"""
import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QScrollArea, QLabel, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QTextCursor

from desktop_app.services.chat_service import ChatService
from desktop_app.services.voice_service import VoiceService
from desktop_app.services.tts_service import TTSService
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()


class ChatThread(QThread):
    """Thread for handling async chat operations"""
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, chat_service, message, chat_id):
        super().__init__()
        self.chat_service = chat_service
        self.message = message
        self.chat_id = chat_id

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.chat_service.send_message(self.message, self.chat_id)
            )
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Error in chat thread: {e}")
            self.error_occurred.emit(str(e))
        finally:
            loop.close()


class VoiceThread(QThread):
    """Thread for handling voice recording"""
    transcription_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, voice_service):
        super().__init__()
        self.voice_service = voice_service

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            text = loop.run_until_complete(
                self.voice_service.record_and_transcribe()
            )
            if text:
                self.transcription_ready.emit(text)
        except Exception as e:
            logger.error(f"Error in voice thread: {e}")
            self.error_occurred.emit(str(e))
        finally:
            loop.close()


class ChatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_service = ChatService()
        self.voice_service = VoiceService()
        self.tts_service = TTSService()
        self.storage = StorageService()
        self.chat_id = None
        self.chat_thread = None
        self.voice_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize the chat interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Top bar with TTS toggle
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setStyleSheet("""
            QFrame#topBar {
                background-color: #111111;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)

        top_label = QLabel("ONYX Chat")
        top_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #4a9eff; background: transparent;")
        top_layout.addWidget(top_label)

        top_layout.addStretch()

        # TTS toggle
        self.tts_checkbox = QCheckBox("Voice Replies")
        self.tts_checkbox.setObjectName("ttsToggle")
        self.tts_checkbox.setToolTip("Enable text-to-speech for AI responses")
        self.tts_checkbox.setChecked(False)
        self.tts_checkbox.stateChanged.connect(self._on_tts_toggled)
        self.tts_checkbox.setStyleSheet("""
            QCheckBox#ttsToggle {
                color: #909090;
                font-size: 13px;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox#ttsToggle:hover {
                color: #e0e0e0;
            }
            QCheckBox#ttsToggle::indicator {
                width: 36px;
                height: 20px;
                border-radius: 10px;
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
            }
            QCheckBox#ttsToggle::indicator:checked {
                background-color: #4a9eff;
                border-color: #4a9eff;
            }
        """)
        top_layout.addWidget(self.tts_checkbox)

        tts_available = self.tts_service.available
        if not tts_available:
            self.tts_checkbox.setEnabled(False)
            self.tts_checkbox.setToolTip("TTS not available — install espeak-ng and pyttsx3")

        layout.addWidget(top_bar)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatArea")
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #e0e0e0;
                border: none;
                font-size: 15px;
                line-height: 1.6;
                padding: 16px;
            }
        """)
        layout.addWidget(self.chat_display, stretch=1)

        # Input area
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #111111;
                border-radius: 16px;
                padding: 8px;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(12)

        # Message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMaximumHeight(120)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 2px solid #252525;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 15px;
            }
            QTextEdit:focus {
                border-color: #4a9eff;
            }
        """)
        input_layout.addWidget(self.message_input, stretch=1)

        # Button container
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)

        # Voice button
        self.voice_button = QPushButton("Mic")
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_button.setToolTip("Push to talk")
        self.voice_button.clicked.connect(self.start_voice_input)
        button_layout.addWidget(self.voice_button)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("primaryButton")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setMinimumWidth(80)
        button_layout.addWidget(self.send_button)

        input_layout.addLayout(button_layout)
        layout.addWidget(input_container)

    def _on_tts_toggled(self, state):
        self.tts_service.enabled = (state == Qt.CheckState.Checked.value)

    def set_chat_id(self, chat_id):
        """Set the current chat ID"""
        self.chat_id = chat_id

    def load_chat(self, chat_id, messages):
        """Load a chat with its message history"""
        self.chat_id = chat_id
        self.chat_display.clear()
        for msg in messages:
            if msg['role'] == 'user':
                self.append_user_message(msg['content'])
            else:
                self.append_assistant_message(msg['content'], speak=False)

    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.clear()
        self.chat_id = None

    def append_user_message(self, text):
        """Append a user message to the chat"""
        escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        self.chat_display.append(f"""
        <div style='margin: 12px 0; text-align: right;'>
            <div style='display: inline-block; background-color: #4a9eff; color: #ffffff;
                        border-radius: 16px; padding: 12px 16px; max-width: 70%; text-align: left;'>
                <strong>You:</strong><br>
                {escaped}
            </div>
        </div>
        """)
        self.scroll_to_bottom()

    def append_assistant_message(self, text, speak=True):
        """Append an assistant message to the chat"""
        escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        self.chat_display.append(f"""
        <div style='margin: 12px 0; text-align: left;'>
            <div style='display: inline-block; background-color: #1a1a1a; color: #e0e0e0;
                        border: 1px solid #252525; border-radius: 16px; padding: 12px 16px;
                        max-width: 70%; text-align: left;'>
                <strong style='color: #4a9eff;'>ONYX:</strong><br>
                {escaped}
            </div>
        </div>
        """)
        self.scroll_to_bottom()

        if speak and self.tts_service.enabled:
            self.tts_service.speak(text)

    def scroll_to_bottom(self):
        """Scroll chat display to bottom"""
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        """Send a message to the AI assistant"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return

        if not self.chat_id:
            self.chat_id = self.storage.create_chat(message[:50])

        self.append_user_message(message)
        self.message_input.clear()

        self.send_button.setEnabled(False)
        self.message_input.setEnabled(False)

        self.chat_thread = ChatThread(self.chat_service, message, self.chat_id)
        self.chat_thread.response_ready.connect(self.on_response_ready)
        self.chat_thread.error_occurred.connect(self.on_error)
        self.chat_thread.start()

        logger.info(f"Sent message in chat {self.chat_id}")

    @Slot(str)
    def on_response_ready(self, response):
        """Handle assistant response"""
        self.append_assistant_message(response, speak=True)
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()

    @Slot(str)
    def on_error(self, error_message):
        """Handle error"""
        self.append_assistant_message(f"Error: {error_message}", speak=False)
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)

    def start_voice_input(self):
        """Start voice recording"""
        if self.voice_thread and self.voice_thread.isRunning():
            return

        self.voice_button.setObjectName("voiceButtonRecording")
        self.voice_button.setStyleSheet(self.voice_button.styleSheet())
        self.voice_button.setText("REC")
        self.voice_button.setEnabled(False)

        self.voice_thread = VoiceThread(self.voice_service)
        self.voice_thread.transcription_ready.connect(self.on_transcription_ready)
        self.voice_thread.error_occurred.connect(self.on_voice_error)
        self.voice_thread.finished.connect(self.on_voice_finished)
        self.voice_thread.start()

        logger.info("Started voice recording")

    @Slot(str)
    def on_transcription_ready(self, text):
        """Handle transcribed text"""
        self.message_input.setPlainText(text)
        logger.info(f"Transcribed: {text}")

    @Slot(str)
    def on_voice_error(self, error_message):
        """Handle voice error"""
        logger.error(f"Voice error: {error_message}")

    def on_voice_finished(self):
        """Handle voice recording finished"""
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.setStyleSheet(self.voice_button.styleSheet())
        self.voice_button.setText("Mic")
        self.voice_button.setEnabled(True)
