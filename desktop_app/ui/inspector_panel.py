"""Inspector panel — right-side state/summary viewer for persistent agent context.
Shows agent state, conversation summary, tasks, events, files, and memory."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer

from desktop_app.ui.styles import (
    BG_DEEP, BG_BASE, BG_SURFACE, BG_RAISED, BG_HOVER,
    BORDER, TEXT_PRI, TEXT_SEC, TEXT_MUTED, ACCENT, ACCENT_DIM,
    SUCCESS, DANGER,
)
from desktop_app.utils.logger import get_logger

logger = get_logger()

SECTION_HEADER_SS = f"""
    QPushButton {{
        background: {BG_BASE};
        color: {ACCENT};
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        text-align: left;
    }}
    QPushButton:hover {{ background: {BG_SURFACE}; }}
"""

ROW_LABEL_SS = f"color:{TEXT_MUTED}; font-size:11px;"
ROW_VALUE_SS = f"color:{TEXT_PRI}; font-size:12px;"
EMPTY_SS = f"color:{TEXT_MUTED}; font-size:11px; font-style:italic; padding:4px 0;"

STATUS_COLORS = {
    "active": SUCCESS,
    "queued": ACCENT,
    "blocked": "#f59e0b",
    "failed": DANGER,
    "completed": TEXT_MUTED,
}


class CollapsibleSection(QFrame):
    """Collapsible section with accent header and content area."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QPushButton(f"  \u25bc  {title}")
        self.header.setStyleSheet(SECTION_HEADER_SS)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.clicked.connect(self.toggle)
        layout.addWidget(self.header)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 6, 12, 8)
        self.content_layout.setSpacing(4)
        layout.addWidget(self.content)

    def toggle(self):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        arrow = "\u25bc" if self._expanded else "\u25b6"
        self.header.setText(f"  {arrow}  {self._title}")

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def add_row(self, label: str, value: str, value_color: str = None):
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 1, 0, 1)
        rl.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet(ROW_LABEL_SS)
        lbl.setFixedWidth(90)
        rl.addWidget(lbl)
        val = QLabel(value)
        color = value_color or TEXT_PRI
        val.setStyleSheet(f"color:{color}; font-size:12px;")
        val.setWordWrap(True)
        rl.addWidget(val, stretch=1)
        self.content_layout.addWidget(row)

    def add_text(self, text: str, color: str = None):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{color or TEXT_SEC}; font-size:12px; padding:2px 0;")
        self.content_layout.addWidget(lbl)

    def add_empty(self, text: str = "No data"):
        lbl = QLabel(text)
        lbl.setStyleSheet(EMPTY_SS)
        self.content_layout.addWidget(lbl)


class InspectorPanel(QWidget):
    """Right-side panel exposing persistent agent state and context summaries."""

    POLL_MS = 15000  # 15 second refresh

    def __init__(self, bridge=None, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self._chat_id = None
        self._chat_title = ""
        self.setObjectName("inspectorPanel")
        self.setMinimumWidth(240)
        self.setMaximumWidth(400)
        self.init_ui()

        self._poll = QTimer(self)
        self._poll.timeout.connect(self.refresh_all)
        self._poll.start(self.POLL_MS)

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(
            f"background:{BG_BASE}; border-bottom:1px solid {BORDER};"
            f" border-left:1px solid {BORDER};"
        )
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 8, 12, 8)
        title = QLabel("INSPECTOR")
        title.setStyleSheet(
            f"font-size:11px; font-weight:800; color:{ACCENT};"
            f" letter-spacing:3px;"
        )
        hl.addWidget(title)
        hl.addStretch()

        self.status_label = QLabel("LOCAL")
        self.status_label.setStyleSheet(
            f"font-size:10px; color:{TEXT_MUTED}; letter-spacing:1px;"
        )
        hl.addWidget(self.status_label)
        root.addWidget(hdr)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ background:{BG_DEEP}; border:none;"
            f" border-left:1px solid {BORDER}; }}"
        )
        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)

        self.sec_agent = CollapsibleSection("AGENT STATE")
        self.sec_summary = CollapsibleSection("CONVERSATION")
        self.sec_tasks = CollapsibleSection("TASKS")
        self.sec_events = CollapsibleSection("EVENTS")
        self.sec_files = CollapsibleSection("FILES")
        self.sec_memory = CollapsibleSection("MEMORY")

        for sec in [self.sec_agent, self.sec_summary, self.sec_tasks,
                    self.sec_events, self.sec_files, self.sec_memory]:
            self._body_layout.addWidget(sec)

        self._body_layout.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        self._populate_defaults()

    def _populate_defaults(self):
        self.sec_agent.add_row("Status", "active", SUCCESS)
        self.sec_agent.add_row("Model", "...")
        self.sec_summary.add_empty("No conversation selected")
        self.sec_tasks.add_empty("No tasks")
        self.sec_events.add_empty("No events")
        self.sec_files.add_empty("No files")
        self.sec_memory.add_empty("No memory data")

    # ── Public API ────────────────────────────────────────────

    def set_conversation(self, chat_id: int, title: str = ""):
        self._chat_id = chat_id
        self._chat_title = title
        self.refresh_all()

    def refresh_all(self):
        self._refresh_status()
        self._refresh_agent()
        self._refresh_summary()
        self._refresh_tasks()
        self._refresh_events()
        self._refresh_files()
        self._refresh_memory()

    # ── Refresh methods ───────────────────────────────────────

    def _refresh_status(self):
        if self.bridge:
            status = self.bridge.status
            if status == "AGENT_READY":
                txt, color = "LETTA READY", SUCCESS
            elif status == "CONNECTED":
                txt, color = "LETTA CONNECTED", ACCENT
            elif status == "NOT_CONFIGURED":
                txt, color = "LETTA NOT SET", TEXT_MUTED
            elif status == "ERROR":
                txt, color = "LETTA ERROR", DANGER
            else:
                txt, color = status, TEXT_MUTED
        else:
            txt, color = "NO BRIDGE", TEXT_MUTED
        self.status_label.setText(txt)
        self.status_label.setStyleSheet(
            f"font-size:10px; color:{color}; letter-spacing:1px;"
        )

    def _refresh_agent(self):
        self.sec_agent.clear_content()
        if not self.bridge:
            self.sec_agent.add_empty("No bridge configured")
            return
        state = self.bridge.get_agent_state()
        status = state.get("status", "unknown")
        color = SUCCESS if status == "AGENT_READY" else TEXT_SEC
        self.sec_agent.add_row("Status", status, color)
        self.sec_agent.add_row("Runtime", "Letta" if self.bridge.agent_ready else "none")
        self.sec_agent.add_row("Agent", state.get("agent_id", "none")[:20])
        self.sec_agent.add_row("Model", state.get("model", "?"))
        detail = state.get("status_detail", "")
        if detail:
            self.sec_agent.add_text(detail[:200], color=TEXT_MUTED)

    def _refresh_summary(self):
        self.sec_summary.clear_content()
        if not self._chat_id:
            self.sec_summary.add_empty("No conversation selected")
            return
        self.sec_summary.add_row("Title", self._chat_title or "Untitled")
        self.sec_summary.add_row("Local ID", str(self._chat_id))

        if self.bridge and self.bridge.agent_ready:
            self.sec_summary.add_row("Runtime", "Letta", SUCCESS)
            self.sec_summary.add_row("Agent", (self.bridge.agent_id or "")[:16])
        elif self.bridge:
            self.sec_summary.add_row("Runtime", self.bridge.status, TEXT_MUTED)
        else:
            self.sec_summary.add_empty("No bridge")

    def _refresh_tasks(self):
        self.sec_tasks.clear_content()
        if not self.bridge:
            self.sec_tasks.add_empty("No bridge")
            return
        tasks = self.bridge.get_tasks()
        if not tasks:
            supabase_ok = (self.bridge.supabase and self.bridge.supabase.available)
            if supabase_ok:
                self.sec_tasks.add_empty("No tasks")
            else:
                self.sec_tasks.add_empty("Configure Supabase for task tracking")
            return
        for t in tasks[:15]:
            status = t.get("status", "active")
            color = STATUS_COLORS.get(status, TEXT_SEC)
            icon = {"active": "\u25cf", "completed": "\u2713",
                    "failed": "\u2717", "queued": "\u25cb",
                    "blocked": "\u25a0"}.get(status, "\u25cf")
            self.sec_tasks.add_text(
                f"{icon} {t.get('title', '?')}",
                color=color,
            )

    def _refresh_events(self):
        self.sec_events.clear_content()
        if not self.bridge:
            self.sec_events.add_empty("No bridge")
            return
        events = self.bridge.get_events(limit=10)
        if not events:
            supabase_ok = (self.bridge.supabase and self.bridge.supabase.available)
            if supabase_ok:
                self.sec_events.add_empty("No events")
            else:
                self.sec_events.add_empty("Configure Supabase for events")
            return
        for e in events[:10]:
            ts = str(e.get("created_at", ""))[:16]
            etype = e.get("event_type", "event")
            content = e.get("content", "")[:80]
            self.sec_events.add_text(
                f"{ts}  {etype}: {content}", color=TEXT_SEC
            )

    def _refresh_files(self):
        self.sec_files.clear_content()
        if not self.bridge:
            self.sec_files.add_empty("No bridge")
            return
        conv_id = str(self._chat_id) if self._chat_id else None
        files = self.bridge.get_files(conversation_id=conv_id)
        if not files:
            supabase_ok = (self.bridge.supabase and self.bridge.supabase.available)
            if supabase_ok:
                self.sec_files.add_empty("No files")
            else:
                self.sec_files.add_empty("Configure Supabase for file tracking")
            return
        for f in files[:15]:
            size = f.get("size", 0)
            sz = f"{size}" if size < 1024 else f"{size / 1024:.1f}KB"
            self.sec_files.add_text(
                f"{f.get('name', '?')} ({sz})", color=TEXT_SEC
            )

    def _refresh_memory(self):
        self.sec_memory.clear_content()
        if not self.bridge:
            self.sec_memory.add_empty("No bridge")
            return
        if not self.bridge.agent_ready:
            self.sec_memory.add_empty(
                "Letta not configured. Memory blocks appear here when connected."
            )
            return

        blocks = self.bridge.get_memory_blocks()
        if not blocks:
            self.sec_memory.add_empty("No memory blocks")
            return
        for b in blocks:
            label = b.get("label", "?")
            value = b.get("value", "")
            limit = b.get("limit", 0)
            # Show label as header, value as content
            header_color = ACCENT if label == "persona" else TEXT_SEC
            self.sec_memory.add_row(
                label.upper(),
                f"({len(value)}/{limit} chars)" if limit else f"({len(value)} chars)",
                header_color,
            )
            if value:
                self.sec_memory.add_text(value[:300], color=TEXT_PRI)
