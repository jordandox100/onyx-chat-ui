"""Inspector panel — right-side state viewer. Supabase-backed, no Letta."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer

from desktop_app.ui.styles import (
    BG_DEEP, BG_BASE, BG_SURFACE, BORDER,
    TEXT_PRI, TEXT_SEC, TEXT_MUTED, ACCENT,
    SUCCESS, DANGER,
)
from desktop_app.utils.logger import get_logger

logger = get_logger()

SECTION_HEADER_SS = f"""
    QPushButton {{
        background: {BG_BASE}; color: {ACCENT}; border: none;
        border-bottom: 1px solid {BORDER}; padding: 8px 12px;
        font-size: 11px; font-weight: 700; letter-spacing: 2px; text-align: left;
    }}
    QPushButton:hover {{ background: {BG_SURFACE}; }}
"""
ROW_LABEL_SS = f"color:{TEXT_MUTED}; font-size:11px;"
EMPTY_SS = f"color:{TEXT_MUTED}; font-size:11px; font-style:italic; padding:4px 0;"
STATUS_COLORS = {"active": SUCCESS, "queued": ACCENT, "blocked": "#f59e0b",
                 "failed": DANGER, "completed": TEXT_MUTED}


class CollapsibleSection(QFrame):
    def __init__(self, title, parent=None):
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
            w = self.content_layout.takeAt(0).widget()
            if w: w.deleteLater()

    def add_row(self, label, value, value_color=None):
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 1, 0, 1); rl.setSpacing(6)
        lbl = QLabel(label); lbl.setStyleSheet(ROW_LABEL_SS); lbl.setFixedWidth(90)
        rl.addWidget(lbl)
        val = QLabel(value); val.setStyleSheet(f"color:{value_color or TEXT_PRI}; font-size:12px;")
        val.setWordWrap(True); rl.addWidget(val, stretch=1)
        self.content_layout.addWidget(row)

    def add_text(self, text, color=None):
        lbl = QLabel(text); lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{color or TEXT_SEC}; font-size:12px; padding:2px 0;")
        self.content_layout.addWidget(lbl)

    def add_empty(self, text="No data"):
        lbl = QLabel(text); lbl.setStyleSheet(EMPTY_SS)
        self.content_layout.addWidget(lbl)


class InspectorPanel(QWidget):
    POLL_MS = 15000

    def __init__(self, runtime=None, supabase=None, parent=None):
        super().__init__(parent)
        self.runtime = runtime
        self.supabase = supabase
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
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet(f"background:{BG_BASE}; border-bottom:1px solid {BORDER}; border-left:1px solid {BORDER};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(12, 8, 12, 8)
        title = QLabel("INSPECTOR")
        title.setStyleSheet(f"font-size:11px; font-weight:800; color:{ACCENT}; letter-spacing:3px;")
        hl.addWidget(title); hl.addStretch()
        self.status_label = QLabel("...")
        self.status_label.setStyleSheet(f"font-size:10px; color:{TEXT_MUTED}; letter-spacing:1px;")
        hl.addWidget(self.status_label)
        root.addWidget(hdr)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ background:{BG_DEEP}; border:none; border-left:1px solid {BORDER}; }}")
        body = QWidget()
        bl = QVBoxLayout(body); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(0)

        self.sec_agent = CollapsibleSection("AGENT STATE")
        self.sec_summary = CollapsibleSection("CONVERSATION")
        self.sec_goals = CollapsibleSection("GOALS")
        self.sec_beliefs = CollapsibleSection("BELIEFS")
        self.sec_tasks = CollapsibleSection("TASKS")
        self.sec_events = CollapsibleSection("EVENTS")
        self.sec_files = CollapsibleSection("FILES")
        self.sec_memory = CollapsibleSection("MEMORIES")

        for sec in [self.sec_agent, self.sec_summary, self.sec_goals,
                    self.sec_beliefs, self.sec_tasks, self.sec_events,
                    self.sec_files, self.sec_memory]:
            bl.addWidget(sec)
        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)
        self._populate_defaults()

    def _populate_defaults(self):
        self.sec_agent.add_row("Status", "..."); self.sec_agent.add_row("Model", "...")
        self.sec_summary.add_empty("No conversation selected")
        self.sec_goals.add_empty("No goals"); self.sec_beliefs.add_empty("No beliefs")
        self.sec_tasks.add_empty("No tasks"); self.sec_events.add_empty("No events")
        self.sec_files.add_empty("No files"); self.sec_memory.add_empty("No memories")

    def set_conversation(self, chat_id, title=""):
        self._chat_id = chat_id; self._chat_title = title
        self.refresh_all()

    def refresh_all(self):
        self._refresh_status(); self._refresh_agent(); self._refresh_summary()
        self._refresh_goals(); self._refresh_beliefs(); self._refresh_tasks()
        self._refresh_events(); self._refresh_files(); self._refresh_memory()

    def _supa_ok(self):
        return self.supabase and self.supabase.available

    # ── Refresh ───────────────────────────────────────────────

    def _refresh_status(self):
        if self.runtime:
            s = self.runtime.status
            color = SUCCESS if s == "READY" else TEXT_MUTED
            self.status_label.setText(s)
            self.status_label.setStyleSheet(f"font-size:10px; color:{color}; letter-spacing:1px;")
        else:
            self.status_label.setText("NO RUNTIME")

    def _refresh_agent(self):
        self.sec_agent.clear_content()
        if not self.runtime:
            self.sec_agent.add_empty("No runtime"); return
        state = self.runtime.get_agent_state()
        self.sec_agent.add_row("Status", state["status"],
                               SUCCESS if state["status"] == "READY" else TEXT_SEC)
        self.sec_agent.add_row("Runtime", state.get("runtime", "?"))
        self.sec_agent.add_row("Model", state.get("model", "?"))
        self.sec_agent.add_row("Supabase", "connected" if self._supa_ok() else "offline",
                               SUCCESS if self._supa_ok() else TEXT_MUTED)

    def _refresh_summary(self):
        self.sec_summary.clear_content()
        if not self._chat_id:
            self.sec_summary.add_empty("No conversation selected"); return
        self.sec_summary.add_row("Title", self._chat_title or "Untitled")
        self.sec_summary.add_row("ID", str(self._chat_id))
        if self.runtime:
            summary = self.runtime.get_conversation_summary(self._chat_id)
            if summary:
                self.sec_summary.add_text(summary[:500])
            else:
                self.sec_summary.add_empty("Summary generates after ~8 messages")

    def _refresh_goals(self):
        self.sec_goals.clear_content()
        if not self.runtime:
            self.sec_goals.add_empty("No runtime"); return
        goals = self.runtime.get_goals()
        if not goals:
            self.sec_goals.add_empty("No goals" if self._supa_ok() else "Configure Supabase")
            return
        for g in goals[:10]:
            s = g.get("status", "active")
            icon = {"active": "\u25cf", "completed": "\u2713", "blocked": "\u25a0"}.get(s, "\u25cf")
            self.sec_goals.add_text(f"{icon} {g.get('title','?')}", STATUS_COLORS.get(s, TEXT_SEC))

    def _refresh_beliefs(self):
        self.sec_beliefs.clear_content()
        if not self.runtime:
            self.sec_beliefs.add_empty("No runtime"); return
        beliefs = self.runtime.get_beliefs()
        if not beliefs:
            self.sec_beliefs.add_empty("No beliefs" if self._supa_ok() else "Configure Supabase")
            return
        for b in beliefs[:10]:
            conf = b.get("confidence", 0)
            self.sec_beliefs.add_text(f"({conf:.0%}) {b.get('content','?')}", TEXT_SEC)

    def _refresh_tasks(self):
        self.sec_tasks.clear_content()
        if not self.runtime:
            self.sec_tasks.add_empty("No runtime"); return
        tasks = self.runtime.get_tasks()
        if not tasks:
            self.sec_tasks.add_empty("No tasks" if self._supa_ok() else "Configure Supabase")
            return
        for t in tasks[:15]:
            s = t.get("status", "active")
            icon = {"active": "\u25cf", "completed": "\u2713", "failed": "\u2717",
                    "queued": "\u25cb", "blocked": "\u25a0"}.get(s, "\u25cf")
            self.sec_tasks.add_text(f"{icon} {t.get('title','?')}", STATUS_COLORS.get(s, TEXT_SEC))

    def _refresh_events(self):
        self.sec_events.clear_content()
        if not self.runtime:
            self.sec_events.add_empty("No runtime"); return
        events = self.runtime.get_events(limit=10)
        if not events:
            self.sec_events.add_empty("No events" if self._supa_ok() else "Configure Supabase")
            return
        for e in events[:10]:
            ts = str(e.get("created_at", ""))[:16]
            self.sec_events.add_text(f"{ts}  {e.get('event_type','')}: {e.get('content','')[:80]}", TEXT_SEC)

    def _refresh_files(self):
        self.sec_files.clear_content()
        if not self.runtime:
            self.sec_files.add_empty("No runtime"); return
        conv_id = str(self._chat_id) if self._chat_id else None
        files = self.runtime.get_files(conversation_id=conv_id)
        if not files:
            self.sec_files.add_empty("No files" if self._supa_ok() else "Configure Supabase")
            return
        for f in files[:15]:
            sz = f.get("size", 0)
            self.sec_files.add_text(f"{f.get('name','?')} ({sz/1024:.1f}KB)", TEXT_SEC)

    def _refresh_memory(self):
        self.sec_memory.clear_content()
        if not self.runtime:
            self.sec_memory.add_empty("No runtime"); return
        memories = self.runtime.get_memories()
        if not memories:
            self.sec_memory.add_empty("No memories" if self._supa_ok() else "Configure Supabase")
            return
        for m in memories[:10]:
            mtype = m.get("memory_type", "fact")
            self.sec_memory.add_text(f"[{mtype}] {m.get('content','')[:200]}", TEXT_SEC)
