"""Chat widget — messages, streaming, model selector, attachments, tools"""
import asyncio
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QFrame, QCheckBox, QComboBox, QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QTextCursor, QColor

from desktop_app.services.chat_service import ChatService, ANTHROPIC_MODELS
from desktop_app.services.voice_service import VoiceService, WakeWordThread, VOICE_AVAILABLE
from desktop_app.services.tts_service import TTSService
from desktop_app.services.storage_service import StorageService
from desktop_app.ui.styles import (
    USER_MSG_HTML, AGENT_MSG_HTML, TOOL_MSG_HTML,
    TYPING_INDICATOR_HTML, ATTACHMENT_HTML,
    BG_DEEP, BG_BASE, BG_SURFACE, BG_RAISED, BORDER,
    TEXT_PRI, TEXT_SEC, TEXT_MUTED, ACCENT, ACCENT_DIM, AGENT_BG,
)
from desktop_app.utils.logger import get_logger

logger = get_logger()

STREAM_MS = 25          # ms per tick
STREAM_CHARS = 4        # chars per tick


class ChatThread(QThread):
    """Background thread for LLM calls + tool execution."""
    tool_output = Signal(str, str, str)   # type, cmd, result
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

            def on_tool(t, cmd, res):
                self.tool_output.emit(t, cmd, res)

            response = loop.run_until_complete(
                self.chat_service.send_message(
                    self.message, self.chat_id, on_tool_output=on_tool,
                )
            )
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Chat thread error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            loop.close()


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


class ChatWidget(QWidget):
    request_refresh_sidebar = Signal()

    def __init__(self):
        super().__init__()
        self.chat_service = ChatService()
        self.voice_service = VoiceService()
        self.tts_service = TTSService()
        self.storage = StorageService()

        self.chat_id = None
        self.chat_thread = None
        self.voice_thread = None
        self.wake_thread = None
        self._attached_files: list[dict] = []

        # Streaming state
        self._stream_text = ""
        self._stream_pos = 0
        self._stream_timer = QTimer(self)
        self._stream_timer.timeout.connect(self._stream_tick)

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
        top_lay.setContentsMargins(16, 8, 16, 8)

        lbl = QLabel("ONYX")
        lbl.setStyleSheet(f"font-size:18px; font-weight:800; color:{ACCENT}; letter-spacing:3px;")
        top_lay.addWidget(lbl)
        top_lay.addStretch()

        # Model selector
        self.model_combo = QComboBox()
        for display, _ in ANTHROPIC_MODELS:
            self.model_combo.addItem(display)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        top_lay.addWidget(QLabel("Model"))
        top_lay.addWidget(self.model_combo)

        top_lay.addSpacing(16)

        # TTS toggle
        self.tts_check = QCheckBox("TTS")
        self.tts_check.setToolTip("Read responses aloud")
        self.tts_check.stateChanged.connect(self._on_tts_toggled)
        if not self.tts_service.available:
            self.tts_check.setEnabled(False)
            self.tts_check.setToolTip("Install espeak-ng + pyttsx3")
        top_lay.addWidget(self.tts_check)

        # Wake word toggle
        self.ww_check = QCheckBox("Wake")
        self.ww_check.setToolTip("Listen for 'Onyx' wake word")
        self.ww_check.stateChanged.connect(self._on_wake_toggled)
        if not VOICE_AVAILABLE:
            self.ww_check.setEnabled(False)
        top_lay.addWidget(self.ww_check)

        root.addWidget(top)

        # ── Chat display ─────────────────────────────────────
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatArea")
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_DEEP};
                color: {TEXT_PRI};
                border: none;
                font-size: 14px;
                padding: 12px;
            }}
        """)
        root.addWidget(self.chat_display, stretch=1)

        # ── Attachment bar (hidden until files attached) ─────
        self.attach_bar = QFrame()
        self.attach_bar.setStyleSheet(f"background:{BG_SURFACE}; border-top:1px solid {BORDER};")
        self.attach_bar.hide()
        self.attach_bar_layout = QHBoxLayout(self.attach_bar)
        self.attach_bar_layout.setContentsMargins(16, 4, 16, 4)
        self.attach_label = QLabel("")
        self.attach_label.setStyleSheet(f"color:{TEXT_SEC}; font-size:12px;")
        self.attach_bar_layout.addWidget(self.attach_label)
        clear_att = QPushButton("x")
        clear_att.setFixedSize(20, 20)
        clear_att.setStyleSheet(f"background:transparent; color:{TEXT_MUTED}; border:none; font-size:14px;")
        clear_att.clicked.connect(self._clear_attachments)
        self.attach_bar_layout.addWidget(clear_att)
        self.attach_bar_layout.addStretch()
        root.addWidget(self.attach_bar)

        # ── Input bar ────────────────────────────────────────
        inp_frame = QFrame()
        inp_frame.setStyleSheet(f"background:{BG_BASE}; border-top:1px solid {BORDER};")
        inp_lay = QHBoxLayout(inp_frame)
        inp_lay.setContentsMargins(12, 10, 12, 10)
        inp_lay.setSpacing(8)

        # Attach button
        self.attach_btn = QPushButton("+")
        self.attach_btn.setObjectName("attachButton")
        self.attach_btn.setToolTip("Attach file")
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.clicked.connect(self._pick_file)
        inp_lay.addWidget(self.attach_btn)

        # Message input
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Message ONYX...")
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
        inp_lay.addWidget(self.msg_input, stretch=1)

        # Voice button
        self.voice_btn = QPushButton("Mic")
        self.voice_btn.setObjectName("voiceButton")
        self.voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_btn.clicked.connect(self._start_voice)
        inp_lay.addWidget(self.voice_btn)

        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setMinimumWidth(70)
        inp_lay.addWidget(self.send_btn)

        root.addWidget(inp_frame)

    # ── Settings persistence ─────────────────────────────────

    def _load_settings(self):
        s = self.storage.get_settings()
        model = s.get("model", {}).get("name", "claude-sonnet-4-6")
        for i, (_, mid) in enumerate(ANTHROPIC_MODELS):
            if mid == model:
                self.model_combo.setCurrentIndex(i)
                break
        self.tts_check.setChecked(s.get("tts", {}).get("enabled", False))

    def _on_model_changed(self, idx):
        if 0 <= idx < len(ANTHROPIC_MODELS):
            _, model_id = ANTHROPIC_MODELS[idx]
            self.chat_service.set_model(model_id)

    def _on_tts_toggled(self, state):
        self.tts_service.enabled = bool(state)

    def _on_wake_toggled(self, state):
        if state and VOICE_AVAILABLE:
            self.wake_thread = WakeWordThread(self.voice_service)
            self.wake_thread.wake_word_detected.connect(self._start_voice)
            self.wake_thread.start()
        elif self.wake_thread:
            self.wake_thread.stop()
            self.wake_thread = None

    # ── Chat operations ──────────────────────────────────────

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id
        self.chat_service.switch_chat(chat_id)

    def load_chat(self, chat_id, messages):
        self.chat_id = chat_id
        self.chat_service.switch_chat(chat_id)
        self.chat_display.clear()
        for m in messages:
            if m["role"] == "user":
                self._show_user_msg(m["content"])
            else:
                self._show_agent_msg(m["content"])

    def clear_chat(self):
        self.chat_display.clear()
        self.chat_id = None

    # ── Message display ──────────────────────────────────────

    def _show_user_msg(self, text):
        escaped = self._esc(text)
        self.chat_display.append(USER_MSG_HTML.replace("{text}", escaped))
        self._scroll()

    def _show_agent_msg(self, text):
        escaped = self._esc(text)
        self.chat_display.append(AGENT_MSG_HTML.replace("{text}", escaped))
        self._scroll()

    def _show_tool_output(self, tool_type, cmd, result):
        cmd_esc = self._esc(cmd[:200])
        res_esc = self._esc(result[:2000])
        html = TOOL_MSG_HTML.replace("{tool_type}", tool_type)\
                            .replace("{tool_cmd}", cmd_esc)\
                            .replace("{tool_result}", res_esc)
        self.chat_display.append(html)
        self._scroll()

    def _show_typing(self):
        self.chat_display.append(TYPING_INDICATOR_HTML)
        self._scroll()

    def _remove_typing(self):
        """Remove the last 'thinking...' indicator."""
        doc = self.chat_display.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
        # Walk back to find the typing div
        for _ in range(10):
            sel = cursor.selectedText()
            if "thinking" in sel.lower():
                cursor.removeSelectedText()
                cursor.deletePreviousChar()
                return
            cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock, QTextCursor.MoveMode.KeepAnchor)

    # ── Streaming ────────────────────────────────────────────

    def _start_streaming(self, full_text):
        self._remove_typing()
        self._stream_text = full_text
        self._stream_pos = 0

        # Insert ONYX header
        self.chat_display.append(
            f'<div style="margin:8px 120px 0 0; padding:12px 16px;'
            f' background-color:{AGENT_BG}; border-left:3px solid {ACCENT};'
            f' border-radius:2px 12px 12px 12px;">'
            f'<span style="color:{ACCENT}; font-weight:700; font-size:11px;'
            f' text-transform:uppercase; letter-spacing:1px;">ONYX</span><br>'
        )

        self._stream_timer.start(STREAM_MS)

    def _stream_tick(self):
        end = min(self._stream_pos + STREAM_CHARS, len(self._stream_text))
        chunk = self._stream_text[self._stream_pos:end]
        self._stream_pos = end

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        self._scroll()

        if self._stream_pos >= len(self._stream_text):
            self._stream_timer.stop()
            # Close the div
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml("</div>")
            self._on_stream_done()

    def _on_stream_done(self):
        self.send_btn.setEnabled(True)
        self.msg_input.setEnabled(True)
        self.msg_input.setFocus()
        if self.tts_service.enabled:
            self.tts_service.speak(self._stream_text)

    # ── Send ─────────────────────────────────────────────────

    def send_message(self):
        text = self.msg_input.toPlainText().strip()
        if not text and not self._attached_files:
            return

        if not self.chat_id:
            self.chat_id = self.storage.create_chat(text[:50] or "Attachment")
            self.request_refresh_sidebar.emit()

        # Build message with attachments
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

        self.send_btn.setEnabled(False)
        self.msg_input.setEnabled(False)

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
        self._show_agent_msg(f"Error: {err}")
        self.send_btn.setEnabled(True)
        self.msg_input.setEnabled(True)

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
                    content = f"(file too large to inline: {size} bytes)"

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

    @staticmethod
    def _esc(text: str) -> str:
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br>"))

    def _scroll(self):
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())
