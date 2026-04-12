"""Chat widget — messages, code blocks, avatar, voice controls, model descriptions"""
import asyncio
import re
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit,
    QPushButton, QLabel, QFrame, QCheckBox, QComboBox,
    QFileDialog, QSlider, QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer, QUrl
from PySide6.QtGui import QTextCursor, QKeyEvent

from desktop_app.services.chat_service import ChatService, ANTHROPIC_MODELS
from desktop_app.services.voice_service import VoiceService, WakeWordThread, VOICE_AVAILABLE
from desktop_app.services.tts_service import TTSService
from desktop_app.services.storage_service import StorageService
from desktop_app.ui.avatar_widget import RobotAvatar
from desktop_app.ui.styles import (
    USER_MSG_HTML, AGENT_MSG_HTML, TOOL_MSG_HTML,
    TYPING_INDICATOR_HTML, ATTACHMENT_HTML, CODE_BLOCK_HTML,
    LOAD_MORE_HTML, SUMMARY_BAR_HTML,
    BG_DEEP, BG_BASE, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRI, TEXT_SEC, TEXT_MUTED, ACCENT, ACCENT_DIM, AGENT_BG,
    DANGER,
)
from desktop_app.utils.logger import get_logger

logger = get_logger()

STREAM_MS = 20
STREAM_CHARS = 5
CODE_FENCE_RE = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)

DISPLAY_RECENT = 20  # Show last N messages on load (rest via "load older")


# ── Custom text input: Enter sends, Shift+Enter newline ──────

class MessageInput(QTextEdit):
    submit = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit.emit()
        else:
            super().keyPressEvent(event)


# ── Background thread for LLM calls ─────────────────────────

class ChatThread(QThread):
    tool_output = Signal(str, str, str)
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, chat_service, message, chat_id):
        super().__init__()
        self.chat_service = chat_service
        self.message = message
        self.chat_id = chat_id
        self.cancel_flag = threading.Event()

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            def on_tool(t, cmd, res):
                self.tool_output.emit(t, cmd, res)

            response = loop.run_until_complete(
                self.chat_service.send_message(
                    self.message, self.chat_id,
                    on_tool_output=on_tool,
                    cancel_flag=self.cancel_flag,
                )
            )
            if not self.cancel_flag.is_set():
                self.response_ready.emit(response)
        except Exception as e:
            if not self.cancel_flag.is_set():
                logger.error(f"Chat thread error: {e}")
                self.error_occurred.emit(str(e))
        finally:
            loop.close()

    def cancel(self):
        self.cancel_flag.set()


class VoiceThread(QThread):
    transcription_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, voice_service, seconds=5):
        super().__init__()
        self.voice_service = voice_service
        self.seconds = seconds

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            text = loop.run_until_complete(
                self.voice_service.record_and_transcribe(self.seconds)
            )
            if text:
                self.transcription_ready.emit(text)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            loop.close()


# ── Code block parsing ───────────────────────────────────────

def parse_segments(text: str, code_store: dict) -> list[dict]:
    """Split response into text and code segments."""
    segments = []
    last_end = 0
    block_id = len(code_store)

    for match in CODE_FENCE_RE.finditer(text):
        before = text[last_end:match.start()].strip()
        if before:
            segments.append({"type": "text", "content": before})

        lang = match.group(1) or "code"
        code = match.group(2)
        key = f"block_{block_id}"
        code_store[key] = code
        segments.append({"type": "code", "lang": lang, "content": code, "key": key})
        block_id += 1
        last_end = match.end()

    remaining = text[last_end:].strip()
    if remaining:
        segments.append({"type": "text", "content": remaining})

    return segments


def text_for_tts(text: str) -> str:
    """Strip code blocks so TTS doesn't read code."""
    return CODE_FENCE_RE.sub("", text).strip()


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))


# ── Main widget ──────────────────────────────────────────────

class ChatWidget(QWidget):
    request_refresh_sidebar = Signal()

    def __init__(self, chat_service=None):
        super().__init__()

        if chat_service:
            self.chat_service = chat_service
            self.storage = chat_service.storage
        else:
            self.chat_service = ChatService()
            self.storage = StorageService()

        self.voice_service = VoiceService()
        self.tts_service = TTSService()

        self.chat_id = None
        self.chat_thread = None
        self.voice_thread = None
        self.wake_thread = None
        self._attached_files: list[dict] = []
        self._is_first_message = False
        self._loading_settings = False
        self._code_blocks: dict[str, str] = {}

        # Lazy loading state
        self._total_msg_count = 0
        self._displayed_offset = 0

        # Streaming state
        self._stream_segments: list[dict] = []
        self._stream_seg_idx = 0
        self._stream_pos = 0
        self._stream_timer = QTimer(self)
        self._stream_timer.timeout.connect(self._stream_tick)

        # Avatar speaking poll
        self._avatar_poll = QTimer(self)
        self._avatar_poll.timeout.connect(self._poll_speaking)
        self._avatar_poll.start(100)

        self.init_ui()
        self._load_settings()

    # ── UI construction ──────────────────────────────────────

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────
        top = QFrame()
        top.setStyleSheet(f"background:{BG_BASE}; border-bottom:1px solid {BORDER};")
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(12, 6, 12, 6)
        top_lay.setSpacing(8)

        # Avatar
        self.avatar = RobotAvatar(size=48)
        top_lay.addWidget(self.avatar)

        # Brand
        lbl = QLabel("ONYX")
        lbl.setStyleSheet(f"font-size:16px; font-weight:800; color:{ACCENT}; letter-spacing:3px;")
        top_lay.addWidget(lbl)
        top_lay.addStretch()

        # Model selector (with descriptions)
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(320)
        for display, _, desc in ANTHROPIC_MODELS:
            self.model_combo.addItem(f"{display}  —  {desc}")
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        top_lay.addWidget(self.model_combo)

        root.addWidget(top)

        # ── Voice control bar ────────────────────────────────
        vc = QFrame()
        vc.setStyleSheet(f"background:{BG_DEEP}; border-bottom:1px solid {BORDER};")
        vc_lay = QHBoxLayout(vc)
        vc_lay.setContentsMargins(12, 4, 12, 4)
        vc_lay.setSpacing(8)

        # TTS toggle
        self.tts_check = QCheckBox("TTS")
        self.tts_check.setToolTip("Read responses aloud")
        self.tts_check.stateChanged.connect(self._on_tts_toggled)
        if not self.tts_service.available:
            self.tts_check.setEnabled(False)
            self.tts_check.setToolTip("No TTS voices")
        vc_lay.addWidget(self.tts_check)

        # Voice selector
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(180)
        voices = self.tts_service.available_voices
        for name, _, _ in voices:
            self.voice_combo.addItem(name)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        if not voices:
            self.voice_combo.setEnabled(False)
        vc_lay.addWidget(self.voice_combo)

        # Preview button
        self.preview_btn = QPushButton("Preview")
        self.preview_btn.setToolTip("Hear this voice")
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.clicked.connect(self._preview_voice)
        if not self.tts_service.available:
            self.preview_btn.setEnabled(False)
        vc_lay.addWidget(self.preview_btn)

        vc_lay.addSpacing(8)

        # Speed label + slider
        spd_lbl = QLabel("Speed")
        spd_lbl.setStyleSheet(f"color:{TEXT_SEC}; font-size:11px;")
        vc_lay.addWidget(spd_lbl)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedWidth(120)
        self.speed_slider.setToolTip("Speech speed (0.5x — 2.0x)")
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        vc_lay.addWidget(self.speed_slider)

        self.speed_label = QLabel("1.0x")
        self.speed_label.setStyleSheet(f"color:{TEXT_SEC}; font-size:11px; min-width:32px;")
        vc_lay.addWidget(self.speed_label)

        vc_lay.addSpacing(8)

        # Stop / Restart speech
        self.speech_stop_btn = QPushButton("Stop Speech")
        self.speech_stop_btn.setToolTip("Stop current speech")
        self.speech_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speech_stop_btn.clicked.connect(self._stop_speech)
        self.speech_stop_btn.setStyleSheet(f"color:{DANGER}; border-color:{DANGER};")
        vc_lay.addWidget(self.speech_stop_btn)

        self.speech_restart_btn = QPushButton("Restart")
        self.speech_restart_btn.setToolTip("Replay last speech")
        self.speech_restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speech_restart_btn.clicked.connect(self._restart_speech)
        vc_lay.addWidget(self.speech_restart_btn)

        vc_lay.addStretch()

        # Wake word toggle
        self.ww_check = QCheckBox("Wake Word")
        self.ww_check.setToolTip("Listen for 'Onyx'")
        self.ww_check.stateChanged.connect(self._on_wake_toggled)
        if not VOICE_AVAILABLE:
            self.ww_check.setEnabled(False)
        vc_lay.addWidget(self.ww_check)

        root.addWidget(vc)

        # ── Chat display (QTextBrowser for clickable links) ──
        self.chat_display = QTextBrowser()
        self.chat_display.setObjectName("chatArea")
        self.chat_display.setOpenLinks(False)
        self.chat_display.anchorClicked.connect(self._on_link_clicked)
        self.chat_display.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {BG_DEEP};
                color: {TEXT_PRI};
                border: none;
                font-size: 14px;
                padding: 12px;
            }}
        """)
        root.addWidget(self.chat_display, stretch=1)

        # ── Attachment bar ───────────────────────────────────
        self.attach_bar = QFrame()
        self.attach_bar.setStyleSheet(f"background:{BG_SURFACE}; border-top:1px solid {BORDER};")
        self.attach_bar.hide()
        ab_lay = QHBoxLayout(self.attach_bar)
        ab_lay.setContentsMargins(16, 4, 16, 4)
        self.attach_label = QLabel("")
        self.attach_label.setStyleSheet(f"color:{TEXT_SEC}; font-size:12px;")
        ab_lay.addWidget(self.attach_label)
        clear_att = QPushButton("x")
        clear_att.setFixedSize(20, 20)
        clear_att.setStyleSheet(f"background:transparent; color:{TEXT_MUTED}; border:none; font-size:14px;")
        clear_att.clicked.connect(self._clear_attachments)
        ab_lay.addWidget(clear_att)
        ab_lay.addStretch()
        root.addWidget(self.attach_bar)

        # ── Input bar ────────────────────────────────────────
        inp_frame = QFrame()
        inp_frame.setStyleSheet(f"background:{BG_BASE}; border-top:1px solid {BORDER};")
        inp_lay = QHBoxLayout(inp_frame)
        inp_lay.setContentsMargins(12, 8, 12, 8)
        inp_lay.setSpacing(8)

        self.attach_btn = QPushButton("+")
        self.attach_btn.setObjectName("attachButton")
        self.attach_btn.setToolTip("Attach file")
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.clicked.connect(self._pick_file)
        inp_lay.addWidget(self.attach_btn)

        self.msg_input = MessageInput()
        self.msg_input.setPlaceholderText("Message ONYX...  (Enter to send, Shift+Enter for new line)")
        self.msg_input.setMaximumHeight(100)
        self.msg_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_SURFACE};
                color: {TEXT_PRI};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QTextEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self.msg_input.submit.connect(self.send_message)
        inp_lay.addWidget(self.msg_input, stretch=1)

        self.voice_btn = QPushButton("Mic")
        self.voice_btn.setObjectName("voiceButton")
        self.voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_btn.clicked.connect(self._start_voice)
        inp_lay.addWidget(self.voice_btn)

        # Send / Stop agent button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._send_or_stop)
        self.send_btn.setMinimumWidth(80)
        inp_lay.addWidget(self.send_btn)

        root.addWidget(inp_frame)

    # ── Settings persistence ─────────────────────────────────

    def _load_settings(self):
        self._loading_settings = True
        s = self.storage.get_settings()

        model = s.get("model", {}).get("name", "claude-sonnet-4-6")
        for i, (_, mid, _) in enumerate(ANTHROPIC_MODELS):
            if mid == model:
                self.model_combo.setCurrentIndex(i)
                break

        self.tts_check.setChecked(s.get("tts", {}).get("enabled", False))

        voice_idx = s.get("tts", {}).get("voice_idx", 0)
        voices = self.tts_service.available_voices
        if 0 <= voice_idx < len(voices):
            self.voice_combo.setCurrentIndex(voice_idx)

        speed = s.get("tts", {}).get("speed", 1.0)
        self.speed_slider.setValue(int(speed * 100))
        self.speed_label.setText(f"{speed:.1f}x")

        self._loading_settings = False

    def _on_model_changed(self, idx):
        if self._loading_settings:
            return
        if 0 <= idx < len(ANTHROPIC_MODELS):
            _, model_id, _ = ANTHROPIC_MODELS[idx]
            self.chat_service.set_model(model_id)

    def _on_tts_toggled(self, state):
        if self._loading_settings:
            return
        self.tts_service.enabled = bool(state)

    def _on_voice_changed(self, idx):
        if self._loading_settings:
            return
        self.tts_service.voice_index = idx

    def _on_speed_changed(self, val):
        speed = val / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
        if not self._loading_settings:
            self.tts_service.speed = speed

    def _preview_voice(self):
        idx = self.voice_combo.currentIndex()
        self.tts_service.preview(idx)

    def _stop_speech(self):
        self.tts_service.stop()

    def _restart_speech(self):
        self.tts_service.restart()

    def _on_wake_toggled(self, state):
        if state and VOICE_AVAILABLE:
            self.wake_thread = WakeWordThread(self.voice_service)
            self.wake_thread.wake_word_detected.connect(self._start_voice)
            self.wake_thread.start()
        elif self.wake_thread:
            self.wake_thread.stop()
            self.wake_thread = None

    def _poll_speaking(self):
        self.avatar.speaking = self.tts_service.is_speaking

    # ── Link click handler (copy code blocks) ────────────────

    def _on_link_clicked(self, url: QUrl):
        if url.scheme() == "copy":
            key = url.host()
            if key in self._code_blocks:
                QApplication.clipboard().setText(self._code_blocks[key])
                logger.info(f"Copied code block {key}")
        elif url.scheme() == "loadmore":
            self._load_older_messages()

    # ── Chat operations ──────────────────────────────────────

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id
        self.chat_service.switch_chat(chat_id)

    def load_chat(self, chat_id, messages=None):
        """Load a conversation with lazy message loading."""
        self.chat_id = chat_id
        self._is_first_message = False
        self._code_blocks.clear()
        self.chat_service.switch_chat(chat_id)
        self.chat_display.clear()

        if messages is None:
            messages = self.storage.get_chat_messages(chat_id)

        self._total_msg_count = len(messages)

        # Only display last DISPLAY_RECENT messages; show "load older" if more
        if self._total_msg_count > DISPLAY_RECENT:
            display_msgs = messages[-DISPLAY_RECENT:]
            self._displayed_offset = self._total_msg_count - DISPLAY_RECENT
            older = self._total_msg_count - DISPLAY_RECENT
            self.chat_display.append(LOAD_MORE_HTML)
            self.chat_display.append(
                SUMMARY_BAR_HTML.replace(
                    "{text}",
                    f"{older} older message{'s' if older != 1 else ''} hidden"
                )
            )
        else:
            display_msgs = messages
            self._displayed_offset = 0

        for m in display_msgs:
            if m["role"] == "user":
                self._show_user_msg(m["content"])
            else:
                self._show_agent_msg_full(m["content"])

    def _load_older_messages(self):
        """Load more historical messages and prepend to display."""
        if not self.chat_id or self._displayed_offset <= 0:
            return

        page_size = min(DISPLAY_RECENT, self._displayed_offset)
        new_offset = max(0, self._displayed_offset - page_size)
        older_msgs = self.storage.get_messages_page(
            self.chat_id, new_offset, page_size
        )
        self._displayed_offset = new_offset

        if not older_msgs:
            return

        # Re-render: clear and reload with more messages
        all_msgs = self.storage.get_chat_messages(self.chat_id)
        start = self._displayed_offset
        display_msgs = all_msgs[start:]

        self.chat_display.clear()
        self._code_blocks.clear()

        if self._displayed_offset > 0:
            self.chat_display.append(LOAD_MORE_HTML)
            self.chat_display.append(
                SUMMARY_BAR_HTML.replace(
                    "{text}",
                    f"{self._displayed_offset} older messages hidden"
                )
            )

        for m in display_msgs:
            if m["role"] == "user":
                self._show_user_msg(m["content"])
            else:
                self._show_agent_msg_full(m["content"])

    def clear_chat(self):
        self.chat_display.clear()
        self._code_blocks.clear()
        self.chat_id = None

    # ── Message display ──────────────────────────────────────

    def _show_user_msg(self, text):
        self.chat_display.append(USER_MSG_HTML.replace("{text}", _esc(text)))
        self._scroll()

    def _show_agent_msg_full(self, text):
        """Render a complete agent message (with code blocks) — for history."""
        segments = parse_segments(text, self._code_blocks)
        if not any(s["type"] == "code" for s in segments):
            self.chat_display.append(AGENT_MSG_HTML.replace("{text}", _esc(text)))
        else:
            self._render_agent_segments(segments)
        self._scroll()

    def _render_agent_segments(self, segments):
        """Render mixed text + code block segments as a single agent message."""
        html_parts = [
            f'<div style="margin:8px 120px 8px 0; padding:12px 16px;'
            f' background-color:{AGENT_BG}; border-left:3px solid {ACCENT};'
            f' border-radius:2px 12px 12px 12px;">'
            f'<span style="color:{ACCENT}; font-weight:700; font-size:11px;'
            f' text-transform:uppercase; letter-spacing:1px;">ONYX</span><br>'
        ]
        for seg in segments:
            if seg["type"] == "text":
                html_parts.append(
                    f'<span style="color:#e4e8ee; font-size:14px; line-height:1.5;">'
                    f'{_esc(seg["content"])}</span>'
                )
            else:
                html_parts.append(
                    CODE_BLOCK_HTML
                    .replace("{lang}", seg["lang"])
                    .replace("{key}", seg["key"])
                    .replace("{code}", _esc(seg["content"]))
                )
        html_parts.append("</div>")
        self.chat_display.append("".join(html_parts))

    def _show_tool_output(self, tool_type, cmd, result):
        html = (TOOL_MSG_HTML
                .replace("{tool_type}", tool_type)
                .replace("{tool_cmd}", _esc(cmd[:200]))
                .replace("{tool_result}", _esc(result[:2000])))
        self.chat_display.append(html)
        self._scroll()

    def _show_typing(self):
        self.chat_display.append(TYPING_INDICATOR_HTML)
        self._scroll()

    def _remove_typing(self):
        doc = self.chat_display.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
        for _ in range(10):
            sel = cursor.selectedText()
            if "thinking" in sel.lower():
                cursor.removeSelectedText()
                cursor.deletePreviousChar()
                return
            cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock, QTextCursor.MoveMode.KeepAnchor)

    # ── Streaming with code block support ────────────────────

    def _start_streaming(self, full_text):
        self._remove_typing()
        self._stream_segments = parse_segments(full_text, self._code_blocks)
        self._stream_seg_idx = 0
        self._stream_pos = 0

        self.chat_display.append(
            f'<div style="margin:8px 120px 0 0; padding:12px 16px;'
            f' background-color:{AGENT_BG}; border-left:3px solid {ACCENT};'
            f' border-radius:2px 12px 12px 12px;">'
            f'<span style="color:{ACCENT}; font-weight:700; font-size:11px;'
            f' text-transform:uppercase; letter-spacing:1px;">ONYX</span><br>'
        )
        self._stream_timer.start(STREAM_MS)

    def _stream_tick(self):
        if self._stream_seg_idx >= len(self._stream_segments):
            self._stream_timer.stop()
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml("</div>")
            self._on_stream_done()
            return

        seg = self._stream_segments[self._stream_seg_idx]

        if seg["type"] == "code":
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            html = (CODE_BLOCK_HTML
                    .replace("{lang}", seg["lang"])
                    .replace("{key}", seg["key"])
                    .replace("{code}", _esc(seg["content"])))
            cursor.insertHtml(html)
            self._stream_seg_idx += 1
            self._stream_pos = 0
            self._scroll()
        else:
            text = seg["content"]
            end = min(self._stream_pos + STREAM_CHARS, len(text))
            chunk = text[self._stream_pos:end]
            self._stream_pos = end

            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(chunk)
            self._scroll()

            if self._stream_pos >= len(text):
                self._stream_seg_idx += 1
                self._stream_pos = 0

    def _on_stream_done(self):
        self._set_running(False)
        self.msg_input.setFocus()
        if self.tts_service.enabled:
            tts_text = ""
            for seg in self._stream_segments:
                if seg["type"] == "text":
                    tts_text += seg["content"] + " "
            tts_text = tts_text.strip()
            if tts_text:
                self.tts_service.speak(tts_text)

    # ── Send / Stop ──────────────────────────────────────────

    def _send_or_stop(self):
        if self.chat_thread and self.chat_thread.isRunning():
            self._stop_agent()
        else:
            self.send_message()

    def _stop_agent(self):
        if self.chat_thread:
            self.chat_thread.cancel()
        self._stream_timer.stop()
        self._remove_typing()
        self.chat_display.append(
            f'<div style="margin:4px 0; padding:6px 12px; color:{TEXT_MUTED}; font-size:12px;">'
            f'[Stopped]</div>'
        )
        self._set_running(False)

    def _set_running(self, running: bool):
        if running:
            self.send_btn.setText("Stop")
            self.send_btn.setObjectName("stopButton")
            self.msg_input.setEnabled(False)
        else:
            self.send_btn.setText("Send")
            self.send_btn.setObjectName("primaryButton")
            self.msg_input.setEnabled(True)
        self.send_btn.style().unpolish(self.send_btn)
        self.send_btn.style().polish(self.send_btn)

    def send_message(self):
        text = self.msg_input.toPlainText().strip()
        if not text and not self._attached_files:
            return

        if not self.chat_id:
            title = text[:50] or "Attachment"
            self.chat_id = self.storage.create_chat(title)
            self._is_first_message = True
            self.request_refresh_sidebar.emit()
        elif self._is_first_message:
            self.storage.update_chat_title(self.chat_id, text[:50])
            self._is_first_message = False
            self.request_refresh_sidebar.emit()

        full_msg = self._build_message_with_attachments(text)
        self._show_user_msg(text)

        if self._attached_files:
            for f in self._attached_files:
                self.chat_display.append(
                    ATTACHMENT_HTML.replace("{filename}", f["name"]).replace("{size}", f["size_str"])
                )
            self._clear_attachments()

        self.msg_input.clear()
        self._show_typing()
        self._set_running(True)

        self.chat_thread = ChatThread(self.chat_service, full_msg, self.chat_id)
        self.chat_thread.tool_output.connect(self._on_tool_output)
        self.chat_thread.response_ready.connect(self._on_response)
        self.chat_thread.error_occurred.connect(self._on_error)
        self.chat_thread.start()

    @Slot(str, str, str)
    def _on_tool_output(self, ttype, cmd, result):
        self._remove_typing()
        self._show_tool_output(ttype, cmd, result)
        self._show_typing()

    @Slot(str)
    def _on_response(self, response):
        self._start_streaming(response)
        self.request_refresh_sidebar.emit()

    @Slot(str)
    def _on_error(self, err):
        self._remove_typing()
        self._show_agent_msg_full(f"Error: {err}")
        self._set_running(False)

    # ── Attachments ──────────────────────────────────────────

    def _pick_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Attach Files")
        for p in paths:
            path = Path(p)
            try:
                size = path.stat().st_size
                content = ""
                if size < 200_000:
                    try:
                        content = path.read_text(errors="replace")
                    except Exception:
                        content = f"(binary file, {size} bytes)"
                else:
                    content = f"(file too large: {size} bytes)"

                size_str = f"{size}" if size < 1024 else f"{size/1024:.1f}KB"
                self._attached_files.append({
                    "name": path.name,
                    "path": str(path),
                    "content": content,
                    "size_str": size_str,
                })
            except Exception as e:
                logger.error(f"Attach error: {e}")

        if self._attached_files:
            names = ", ".join(f["name"] for f in self._attached_files)
            self.attach_label.setText(f"Attached: {names}")
            self.attach_bar.show()

    def _clear_attachments(self):
        self._attached_files.clear()
        self.attach_bar.hide()

    def _build_message_with_attachments(self, text: str) -> str:
        if not self._attached_files:
            return text
        parts = []
        for f in self._attached_files:
            parts.append(f"[Attached file: {f['name']} ({f['size_str']})]\n{f['content']}\n")
        parts.append(text)
        return "\n".join(parts)

    # ── Voice ────────────────────────────────────────────────

    def _start_voice(self):
        if self.voice_thread and self.voice_thread.isRunning():
            return
        self.voice_btn.setObjectName("voiceButtonRecording")
        self.voice_btn.style().unpolish(self.voice_btn)
        self.voice_btn.style().polish(self.voice_btn)
        self.voice_btn.setText("REC")
        self.voice_btn.setEnabled(False)

        self.voice_thread = VoiceThread(self.voice_service)
        self.voice_thread.transcription_ready.connect(self._on_transcription)
        self.voice_thread.error_occurred.connect(self._on_voice_error)
        self.voice_thread.finished.connect(self._on_voice_done)
        self.voice_thread.start()

    @Slot(str)
    def _on_transcription(self, text):
        self.msg_input.setPlainText(text)

    @Slot(str)
    def _on_voice_error(self, err):
        logger.error(f"Voice error: {err}")

    def _on_voice_done(self):
        self.voice_btn.setObjectName("voiceButton")
        self.voice_btn.style().unpolish(self.voice_btn)
        self.voice_btn.style().polish(self.voice_btn)
        self.voice_btn.setText("Mic")
        self.voice_btn.setEnabled(True)

    # ── Helpers ──────────────────────────────────────────────

    def _scroll(self):
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())
