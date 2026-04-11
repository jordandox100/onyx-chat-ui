"""Main window — sidebar, inspector panel, tray icon, compact toggle"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QInputDialog,
    QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from pathlib import Path

from desktop_app.ui.chat_widget import ChatWidget
from desktop_app.ui.inspector_panel import InspectorPanel
from desktop_app.ui.styles import MAIN_STYLE, BG_BASE, BG_DEEP, BORDER, TEXT_SEC, TEXT_MUTED, ACCENT
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()

ICON_PATH = str(Path(__file__).parent.parent.parent / "install" / "onyx_icon.png")


class MainWindow(QMainWindow):
    def __init__(self, bridge=None):
        super().__init__()
        self.bridge = bridge
        self.storage = bridge.chat.storage if (bridge and bridge.chat) else StorageService()
        self.current_chat_id = None
        self.is_compact = False
        self.inspector_visible = True
        self.init_ui()
        self.init_tray()
        self.load_chats()

    # ── UI ───────────────────────────────────────────────────

    def init_ui(self):
        self.setWindowTitle("ONYX")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(500, 350)
        self.setStyleSheet(MAIN_STYLE)

        icon_file = Path(ICON_PATH)
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))

        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Compact toggle strip
        toggle_strip = QWidget()
        toggle_strip.setFixedWidth(28)
        toggle_strip.setStyleSheet(f"background:{BG_BASE}; border-right:1px solid {BORDER};")
        tl = QVBoxLayout(toggle_strip)
        tl.setContentsMargins(0, 8, 0, 8)
        tl.setSpacing(4)

        self.compact_btn = QPushButton("<")
        self.compact_btn.setObjectName("compactToggle")
        self.compact_btn.setToolTip("Toggle sidebar")
        self.compact_btn.clicked.connect(self.toggle_compact)
        tl.addWidget(self.compact_btn)
        tl.addStretch()
        main_lay.addWidget(toggle_strip)

        # Splitter: sidebar | chat | inspector
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar_widget = self._build_sidebar()
        self.splitter.addWidget(self.sidebar_widget)

        self.chat_widget = ChatWidget(bridge=self.bridge)
        self.chat_widget.request_refresh_sidebar.connect(self.load_chats)
        self.splitter.addWidget(self.chat_widget)

        self.inspector = InspectorPanel(bridge=self.bridge)
        self.splitter.addWidget(self.inspector)

        self.splitter.setSizes([250, 850, 300])
        self.splitter.setStretchFactor(1, 1)
        main_lay.addWidget(self.splitter)

        # Inspector toggle strip (right side)
        rtoggle = QWidget()
        rtoggle.setFixedWidth(28)
        rtoggle.setStyleSheet(f"background:{BG_BASE}; border-left:1px solid {BORDER};")
        rt_lay = QVBoxLayout(rtoggle)
        rt_lay.setContentsMargins(0, 8, 0, 8)
        rt_lay.setSpacing(4)
        self.inspector_btn = QPushButton(">")
        self.inspector_btn.setObjectName("inspectorToggle")
        self.inspector_btn.setToolTip("Toggle inspector")
        self.inspector_btn.clicked.connect(self.toggle_inspector)
        rt_lay.addWidget(self.inspector_btn)
        rt_lay.addStretch()
        main_lay.addWidget(rtoggle)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(220)
        sidebar.setMaximumWidth(380)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 16, 12, 12)
        lay.setSpacing(8)

        # Brand
        brand = QLabel("ONYX")
        brand.setStyleSheet(f"""
            font-size:24px; font-weight:800; color:{ACCENT};
            padding:8px 4px; letter-spacing:4px;
        """)
        lay.addWidget(brand)

        # New chat
        new_btn = QPushButton("+ New Chat")
        new_btn.setObjectName("primaryButton")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.new_chat)
        lay.addWidget(new_btn)

        # Section label
        hist = QLabel("HISTORY")
        hist.setStyleSheet(f"font-size:10px; font-weight:700; color:{TEXT_MUTED}; padding:10px 4px 2px; letter-spacing:2px;")
        lay.addWidget(hist)

        # Chat list
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_selected_chat)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self._context_menu)
        lay.addWidget(self.chat_list)

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_chat)
        btn_row.addWidget(rename_btn)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_chat)
        btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)

        return sidebar

    # ── System tray ──────────────────────────────────────────

    def init_tray(self):
        icon_file = Path(ICON_PATH)
        icon = QIcon(str(icon_file)) if icon_file.exists() else QIcon()

        self.tray_icon = QSystemTrayIcon(icon, self)

        menu = QMenu()
        show_act = QAction("Show ONYX", self)
        show_act.triggered.connect(self._show_window)
        menu.addAction(show_act)
        menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self._quit)
        menu.addAction(quit_act)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.setToolTip("ONYX AI Assistant")
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._show_window()

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit(self):
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    # ── Compact mode ─────────────────────────────────────────

    def toggle_compact(self):
        if self.is_compact:
            self.sidebar_widget.show()
            self.compact_btn.setText("<")
            self.compact_btn.setToolTip("Hide sidebar")
            self.resize(1400, 900)
        else:
            self.sidebar_widget.hide()
            self.compact_btn.setText(">")
            self.compact_btn.setToolTip("Show sidebar")
            self.resize(700, 500)
        self.is_compact = not self.is_compact

    def toggle_inspector(self):
        if self.inspector.isVisible():
            self.inspector.hide()
            self.inspector_btn.setText("<")
            self.inspector_btn.setToolTip("Show inspector")
        else:
            self.inspector.show()
            self.inspector_btn.setText(">")
            self.inspector_btn.setToolTip("Hide inspector")

    # ── Chat management ──────────────────────────────────────

    def load_chats(self):
        self.chat_list.clear()
        for chat in self.storage.get_all_chats():
            self.chat_list.addItem(chat["title"])
            item = self.chat_list.item(self.chat_list.count() - 1)
            item.setData(Qt.ItemDataRole.UserRole, chat["id"])

    def new_chat(self):
        cid = self.storage.create_chat("New Chat")
        self.current_chat_id = cid
        self.load_chats()
        self.chat_widget.clear_chat()
        self.chat_widget.set_chat_id(cid)
        self.chat_widget._is_first_message = True

    def load_selected_chat(self, item):
        cid = item.data(Qt.ItemDataRole.UserRole)
        self.current_chat_id = cid
        msgs = self.storage.get_chat_messages(cid)
        self.chat_widget.load_chat(cid, msgs)
        self.inspector.set_conversation(cid, title=item.text())

    def rename_chat(self):
        cur = self.chat_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "No Selection", "Select a chat first.")
            return
        cid = cur.data(Qt.ItemDataRole.UserRole)
        new_title, ok = QInputDialog.getText(self, "Rename", "New name:", text=cur.text())
        if ok and new_title:
            self.storage.update_chat_title(cid, new_title)
            self.load_chats()

    def delete_chat(self):
        cur = self.chat_list.currentItem()
        if not cur:
            QMessageBox.warning(self, "No Selection", "Select a chat first.")
            return
        cid = cur.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Delete", "Delete this chat?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.storage.delete_chat(cid)
            self.load_chats()
            if cid == self.current_chat_id:
                self.chat_widget.clear_chat()
                self.current_chat_id = None

    def _context_menu(self, pos):
        menu = QMenu(self)
        rename_act = menu.addAction("Rename")
        rename_act.triggered.connect(self.rename_chat)
        del_act = menu.addAction("Delete")
        del_act.triggered.connect(self.delete_chat)
        menu.exec(self.chat_list.mapToGlobal(pos))
