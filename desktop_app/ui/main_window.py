"""Main window — sidebar (chats + shared), inspector, admin panel, tray"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QInputDialog,
    QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QApplication,
    QDialog, QTextEdit, QFrame, QLineEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from pathlib import Path

from desktop_app.ui.chat_widget import ChatWidget
from desktop_app.ui.inspector_panel import InspectorPanel
from desktop_app.ui.styles import (
    MAIN_STYLE, BG_BASE, BG_DEEP, BG_SURFACE, BORDER,
    TEXT_PRI, TEXT_SEC, TEXT_MUTED, ACCENT, DANGER, SUCCESS,
)
from desktop_app.services.storage_service import StorageService
from desktop_app.utils.logger import get_logger

logger = get_logger()

ICON_PATH = str(Path(__file__).parent.parent.parent / "install" / "onyx_icon.png")


class MainWindow(QMainWindow):
    def __init__(self, runtime=None, chat_service=None, supabase=None,
                 auth=None, shared=None, subs=None, username="local"):
        super().__init__()
        self.runtime = runtime
        self.supabase = supabase
        self.auth = auth
        self.shared = shared
        self.subs = subs
        self.username = username
        self._chat_service = chat_service
        self.storage = chat_service.storage if chat_service else StorageService()
        self.current_chat_id = None
        self.is_compact = False
        self.init_ui()
        self.init_tray()
        self.load_chats()
        self._load_shared_folders()

    @property
    def is_admin(self) -> bool:
        return bool(self.auth and self.auth.is_admin)

    def init_ui(self):
        self.setWindowTitle(f"ONYX — {self.username}")
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

        # Toggle strip
        toggle_strip = QWidget()
        toggle_strip.setFixedWidth(28)
        toggle_strip.setStyleSheet(f"background:{BG_BASE}; border-right:1px solid {BORDER};")
        tl = QVBoxLayout(toggle_strip)
        tl.setContentsMargins(0, 8, 0, 8)
        self.compact_btn = QPushButton("<")
        self.compact_btn.setObjectName("compactToggle")
        self.compact_btn.clicked.connect(self.toggle_compact)
        tl.addWidget(self.compact_btn)
        tl.addStretch()
        main_lay.addWidget(toggle_strip)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar_widget = self._build_sidebar()
        self.splitter.addWidget(self.sidebar_widget)

        self.chat_widget = ChatWidget(chat_service=self._chat_service)
        self.chat_widget.request_refresh_sidebar.connect(self.load_chats)
        self.splitter.addWidget(self.chat_widget)

        self.inspector = InspectorPanel(runtime=self.runtime, supabase=self.supabase)
        self.splitter.addWidget(self.inspector)

        self.splitter.setSizes([260, 840, 300])
        self.splitter.setStretchFactor(1, 1)
        main_lay.addWidget(self.splitter)

        # Inspector toggle
        rtoggle = QWidget()
        rtoggle.setFixedWidth(28)
        rtoggle.setStyleSheet(f"background:{BG_BASE}; border-left:1px solid {BORDER};")
        rt_lay = QVBoxLayout(rtoggle)
        rt_lay.setContentsMargins(0, 8, 0, 8)
        self.inspector_btn = QPushButton(">")
        self.inspector_btn.setObjectName("inspectorToggle")
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
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(6)

        # Brand + user
        hdr = QHBoxLayout()
        brand = QLabel("ONYX")
        brand.setStyleSheet(f"font-size:22px; font-weight:800; color:{ACCENT}; letter-spacing:4px;")
        hdr.addWidget(brand)
        hdr.addStretch()
        user_lbl = QLabel(self.username)
        user_lbl.setStyleSheet(f"font-size:11px; color:{TEXT_MUTED};")
        hdr.addWidget(user_lbl)
        lay.addLayout(hdr)

        # Admin button
        if self.is_admin:
            admin_btn = QPushButton("Admin Panel")
            admin_btn.setStyleSheet(
                f"background:{DANGER}; color:white; border:none; border-radius:4px;"
                f" padding:6px; font-size:11px; font-weight:700;"
            )
            admin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            admin_btn.clicked.connect(self._open_admin)
            lay.addWidget(admin_btn)

        new_btn = QPushButton("+ New Chat")
        new_btn.setObjectName("primaryButton")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.new_chat)
        lay.addWidget(new_btn)

        # Chat history
        lbl = QLabel("CHATS")
        lbl.setStyleSheet(f"font-size:10px; font-weight:700; color:{TEXT_MUTED}; padding:8px 4px 2px; letter-spacing:2px;")
        lay.addWidget(lbl)

        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_selected_chat)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self._chat_context)
        lay.addWidget(self.chat_list)

        # Shared folders section
        shared_lbl = QLabel("SHARED FOLDERS")
        shared_lbl.setStyleSheet(f"font-size:10px; font-weight:700; color:{TEXT_MUTED}; padding:8px 4px 2px; letter-spacing:2px;")
        lay.addWidget(shared_lbl)

        share_btn = QPushButton("+ Share with User")
        share_btn.setStyleSheet(
            f"background:{BG_SURFACE}; color:{ACCENT}; border:1px solid {BORDER};"
            f" border-radius:4px; padding:5px; font-size:11px;"
        )
        share_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        share_btn.clicked.connect(self._create_shared_folder)
        lay.addWidget(share_btn)

        self.shared_list = QListWidget()
        self.shared_list.setMaximumHeight(150)
        self.shared_list.itemClicked.connect(self._open_shared_folder)
        lay.addWidget(self.shared_list)

        # Logout
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(
            f"background:transparent; color:{TEXT_MUTED}; border:1px solid {BORDER};"
            f" border-radius:4px; padding:5px; font-size:11px;"
        )
        logout_btn.clicked.connect(self._logout)
        lay.addWidget(logout_btn)

        # Subscription status
        self.sub_frame = QFrame()
        self.sub_frame.setStyleSheet(
            f"background:{BG_SURFACE}; border:1px solid {BORDER}; border-radius:6px;"
        )
        sf_lay = QVBoxLayout(self.sub_frame)
        sf_lay.setContentsMargins(8, 6, 8, 6)
        sf_lay.setSpacing(4)
        self.tier_label = QLabel("...")
        self.tier_label.setStyleSheet(f"color:{ACCENT}; font-size:12px; font-weight:700;")
        sf_lay.addWidget(self.tier_label)
        self.token_label = QLabel("")
        self.token_label.setStyleSheet(f"color:{TEXT_MUTED}; font-size:10px;")
        sf_lay.addWidget(self.token_label)

        up_row = QHBoxLayout()
        up_row.setSpacing(4)
        pro_btn = QPushButton("Pro $19.99")
        pro_btn.setStyleSheet(
            f"background:transparent; color:{SUCCESS}; border:1px solid {SUCCESS};"
            f" border-radius:4px; padding:4px 6px; font-size:10px;"
        )
        pro_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pro_btn.clicked.connect(lambda: self._upgrade("pro"))
        up_row.addWidget(pro_btn)
        builder_btn = QPushButton("Builder $34.99")
        builder_btn.setStyleSheet(
            f"background:transparent; color:#f59e0b; border:1px solid #f59e0b;"
            f" border-radius:4px; padding:4px 6px; font-size:10px;"
        )
        builder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        builder_btn.clicked.connect(lambda: self._upgrade("builder"))
        up_row.addWidget(builder_btn)
        sf_lay.addLayout(up_row)

        tokens_btn = QPushButton("Buy Tokens")
        tokens_btn.setStyleSheet(
            f"background:transparent; color:{TEXT_SEC}; border:1px solid {BORDER};"
            f" border-radius:4px; padding:4px; font-size:10px;"
        )
        tokens_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tokens_btn.clicked.connect(self._buy_tokens)
        sf_lay.addWidget(tokens_btn)
        lay.addWidget(self.sub_frame)
        self._refresh_sub_display()

        return sidebar

    # ── Tray ──────────────────────────────────────────────────

    def init_tray(self):
        icon_file = Path(ICON_PATH)
        icon = QIcon(str(icon_file)) if icon_file.exists() else QIcon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        menu = QMenu()
        menu.addAction("Show", self._show_window)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.setToolTip("ONYX")
        self.tray_icon.show()

    def _show_window(self):
        self.show(); self.raise_(); self.activateWindow()

    def _quit(self):
        self.tray_icon.hide(); QApplication.quit()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide(); event.ignore()
        else:
            event.accept()

    # ── Toggles ───────────────────────────────────────────────

    def toggle_compact(self):
        self.is_compact = not self.is_compact
        self.sidebar_widget.setVisible(not self.is_compact)
        self.compact_btn.setText(">" if self.is_compact else "<")

    def toggle_inspector(self):
        vis = self.inspector.isVisible()
        self.inspector.setVisible(not vis)
        self.inspector_btn.setText("<" if vis else ">")

    # ── Chat management ───────────────────────────────────────

    def load_chats(self):
        self.chat_list.clear()
        for chat in self.storage.get_all_chats():
            item = QListWidgetItem(chat["title"])
            item.setData(Qt.ItemDataRole.UserRole, chat["id"])
            self.chat_list.addItem(item)

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
        self.chat_widget.load_chat(cid)
        self.inspector.set_conversation(cid, title=item.text())

    def _chat_context(self, pos):
        menu = QMenu(self)
        menu.addAction("Rename", self._rename_chat)
        menu.addAction("Delete", self._delete_chat)
        menu.exec(self.chat_list.mapToGlobal(pos))

    def _rename_chat(self):
        cur = self.chat_list.currentItem()
        if not cur: return
        cid = cur.data(Qt.ItemDataRole.UserRole)
        title, ok = QInputDialog.getText(self, "Rename", "New name:", text=cur.text())
        if ok and title:
            self.storage.update_chat_title(cid, title)
            self.load_chats()

    def _delete_chat(self):
        cur = self.chat_list.currentItem()
        if not cur: return
        cid = cur.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Delete", "Delete this chat?") == QMessageBox.StandardButton.Yes:
            self.storage.delete_chat(cid)
            self.load_chats()
            if cid == self.current_chat_id:
                self.chat_widget.clear_chat()
                self.current_chat_id = None

    # ── Shared Folders ────────────────────────────────────────

    def _load_shared_folders(self):
        self.shared_list.clear()
        if not self.shared:
            return
        folders = self.shared.get_folders_for_user(self.username)
        for f in folders:
            owner = f.get("owner_username", "?")
            partner = f.get("partner_username", "?")
            other = partner if owner == self.username else owner
            name = f.get("name", "Shared")
            item = QListWidgetItem(f"{name} (with {other})")
            item.setData(Qt.ItemDataRole.UserRole, f.get("id"))
            self.shared_list.addItem(item)

    def _create_shared_folder(self):
        partner, ok = QInputDialog.getText(
            self, "Share Folder", "Enter other user's username:"
        )
        if not ok or not partner.strip():
            return
        partner = partner.strip()
        if partner == self.username:
            QMessageBox.warning(self, "Error", "Cannot share with yourself")
            return
        name, ok2 = QInputDialog.getText(
            self, "Folder Name", "Name for shared folder:", text="Shared"
        )
        if not ok2: return
        result = self.shared.create_folder(self.username, partner, name or "Shared")
        if result:
            self._load_shared_folders()
        else:
            QMessageBox.warning(self, "Error", "Could not create folder. Check username exists.")

    def _open_shared_folder(self, item):
        folder_id = item.data(Qt.ItemDataRole.UserRole)
        if not folder_id: return
        items = self.shared.get_items(folder_id)
        dlg = QDialog(self)
        dlg.setWindowTitle(item.text())
        dlg.setMinimumSize(500, 400)
        dlg.setStyleSheet(f"background:{BG_DEEP}; color:{TEXT_PRI};")
        lay = QVBoxLayout(dlg)

        # Items list
        item_list = QListWidget()
        for si in items:
            by = si.get("added_by", "?")
            content = si.get("content", "")[:100]
            li = QListWidgetItem(f"[{by}] {content}")
            li.setData(Qt.ItemDataRole.UserRole, si)
            item_list.addItem(li)
        lay.addWidget(item_list)

        # Add item
        add_row = QHBoxLayout()
        add_input = QLineEdit()
        add_input.setPlaceholderText("Add item to shared folder...")
        add_input.setStyleSheet(
            f"background:{BG_SURFACE}; color:{TEXT_PRI}; border:1px solid {BORDER};"
            f" border-radius:4px; padding:8px; font-size:13px;"
        )
        add_row.addWidget(add_input)
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(
            f"background:{ACCENT}; color:{BG_DEEP}; border:none;"
            f" border-radius:4px; padding:8px 16px; font-weight:700;"
        )
        add_btn.clicked.connect(lambda: self._add_shared_item(
            folder_id, add_input.text(), item_list, add_input
        ))
        add_row.addWidget(add_btn)
        lay.addLayout(add_row)

        # Delete button
        del_btn = QPushButton("Delete Selected (own items only)")
        del_btn.setStyleSheet(
            f"background:transparent; color:{DANGER}; border:1px solid {DANGER};"
            f" border-radius:4px; padding:6px; font-size:11px;"
        )
        del_btn.clicked.connect(lambda: self._del_shared_item(folder_id, item_list))
        lay.addWidget(del_btn)

        dlg.exec()

    def _add_shared_item(self, folder_id, text, item_list, input_widget):
        if not text.strip(): return
        from PySide6.QtWidgets import QLineEdit
        self.shared.add_item(folder_id, self.username, text.strip())
        input_widget.clear()
        # Refresh
        item_list.clear()
        for si in self.shared.get_items(folder_id):
            by = si.get("added_by", "?")
            content = si.get("content", "")[:100]
            li = QListWidgetItem(f"[{by}] {content}")
            li.setData(Qt.ItemDataRole.UserRole, si)
            item_list.addItem(li)

    def _del_shared_item(self, folder_id, item_list):
        cur = item_list.currentItem()
        if not cur: return
        si = cur.data(Qt.ItemDataRole.UserRole)
        if not si: return
        self.shared.delete_item(si["id"], self.username, self.is_admin)
        # Refresh
        item_list.clear()
        for si in self.shared.get_items(folder_id):
            by = si.get("added_by", "?")
            content = si.get("content", "")[:100]
            li = QListWidgetItem(f"[{by}] {content}")
            li.setData(Qt.ItemDataRole.UserRole, si)
            item_list.addItem(li)

    # ── Admin Panel ───────────────────────────────────────────

    def _open_admin(self):
        if not self.is_admin:
            return
        users = self.auth.get_all_users()
        dlg = QDialog(self)
        dlg.setWindowTitle("Admin Panel")
        dlg.setMinimumSize(600, 500)
        dlg.setStyleSheet(f"background:{BG_DEEP}; color:{TEXT_PRI};")
        lay = QVBoxLayout(dlg)

        title = QLabel("ADMIN PANEL")
        title.setStyleSheet(f"font-size:16px; font-weight:800; color:{DANGER}; letter-spacing:3px; padding:8px;")
        lay.addWidget(title)

        lbl = QLabel(f"Users: {len(users)}")
        lbl.setStyleSheet(f"color:{TEXT_SEC}; font-size:12px; padding:4px;")
        lay.addWidget(lbl)

        user_list = QListWidget()
        for u in users:
            tag = " [ADMIN]" if u.get("is_admin") else ""
            li = QListWidgetItem(f"{u.get('username', '?')}{tag}")
            li.setData(Qt.ItemDataRole.UserRole, u)
            user_list.addItem(li)
        lay.addWidget(user_list)

        info = QLabel("Click a user to view their data")
        info.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px;")
        lay.addWidget(info)

        view_btn = QPushButton("View User Data")
        view_btn.setStyleSheet(
            f"background:{ACCENT}; color:{BG_DEEP}; border:none;"
            f" border-radius:4px; padding:8px; font-weight:700;"
        )
        view_btn.clicked.connect(lambda: self._view_user_data(user_list))
        lay.addWidget(view_btn)

        # Subscription management
        sub_row = QHBoxLayout()
        sub_pro = QPushButton("Set Pro")
        sub_pro.setStyleSheet(
            f"background:{SUCCESS}; color:{BG_DEEP}; border:none;"
            f" border-radius:4px; padding:6px; font-size:11px; font-weight:700;"
        )
        sub_pro.clicked.connect(lambda: self._admin_set_sub(user_list, "pro"))
        sub_row.addWidget(sub_pro)

        sub_builder = QPushButton("Set Builder")
        sub_builder.setStyleSheet(
            f"background:#f59e0b; color:{BG_DEEP}; border:none;"
            f" border-radius:4px; padding:6px; font-size:11px; font-weight:700;"
        )
        sub_builder.clicked.connect(lambda: self._admin_set_sub(user_list, "builder"))
        sub_row.addWidget(sub_builder)

        sub_free = QPushButton("Set Free")
        sub_free.setStyleSheet(
            f"background:{TEXT_MUTED}; color:{BG_DEEP}; border:none;"
            f" border-radius:4px; padding:6px; font-size:11px; font-weight:700;"
        )
        sub_free.clicked.connect(lambda: self._admin_set_sub(user_list, "free"))
        sub_row.addWidget(sub_free)

        add_tok = QPushButton("+500 Tokens")
        add_tok.setStyleSheet(
            f"background:{ACCENT}; color:{BG_DEEP}; border:none;"
            f" border-radius:4px; padding:6px; font-size:11px; font-weight:700;"
        )
        add_tok.clicked.connect(lambda: self._admin_add_tokens(user_list, 500))
        sub_row.addWidget(add_tok)
        lay.addLayout(sub_row)

        dlg.exec()

    def _admin_set_sub(self, user_list, tier):
        cur = user_list.currentItem()
        if not cur: return
        u = cur.data(Qt.ItemDataRole.UserRole)
        uname = u.get("username", "?")
        if self.subs and self.subs.set_subscription(uname, tier):
            QMessageBox.information(self, "Done", f"{uname} set to {tier.upper()}")
            self._refresh_sub_display()
        else:
            QMessageBox.warning(self, "Error", "Failed to update subscription")

    def _admin_add_tokens(self, user_list, amount):
        cur = user_list.currentItem()
        if not cur: return
        u = cur.data(Qt.ItemDataRole.UserRole)
        uname = u.get("username", "?")
        if self.subs and self.subs.add_tokens(uname, amount):
            QMessageBox.information(self, "Done", f"Added {amount} tokens to {uname}")
        else:
            QMessageBox.warning(self, "Error", "Failed (user may need Builder tier first)")

    def _view_user_data(self, user_list):
        cur = user_list.currentItem()
        if not cur: return
        u = cur.data(Qt.ItemDataRole.UserRole)
        uname = u.get("username", "?")
        if not self.supabase or not self.supabase.available:
            return

        # Fetch user's data
        lines = [f"=== User: {uname} ===\n"]
        memories = self.supabase.get_memories(uname, limit=20)
        lines.append(f"\nMemories ({len(memories)}):")
        for m in memories:
            lines.append(f"  - {m.get('content','')[:100]}")

        beliefs = self.supabase.get_beliefs(uname)
        lines.append(f"\nBeliefs ({len(beliefs)}):")
        for b in beliefs:
            lines.append(f"  - ({b.get('confidence',0):.0%}) {b.get('content','')[:100]}")

        goals = self.supabase.get_goals(uname)
        lines.append(f"\nGoals ({len(goals)}):")
        for g in goals:
            lines.append(f"  - [{g.get('status','?')}] {g.get('title','')}")

        tasks = self.supabase.get_tasks(uname)
        lines.append(f"\nTasks ({len(tasks)}):")
        for t in tasks:
            lines.append(f"  - [{t.get('status','?')}] {t.get('title','')}")

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Data: {uname}")
        dlg.setMinimumSize(500, 400)
        dlg.setStyleSheet(f"background:{BG_DEEP}; color:{TEXT_PRI};")
        lay = QVBoxLayout(dlg)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText("\n".join(lines))
        txt.setStyleSheet(
            f"background:{BG_SURFACE}; color:{TEXT_PRI}; border:1px solid {BORDER};"
            f" font-family:monospace; font-size:12px;"
        )
        lay.addWidget(txt)
        dlg.exec()

    # ── Logout ────────────────────────────────────────────────

    def _logout(self):
        if self.auth:
            self.auth.logout()
        self.tray_icon.hide()
        QApplication.quit()

    # ── Subscription ──────────────────────────────────────────

    def _refresh_sub_display(self):
        if not self.subs:
            self.tier_label.setText("FREE")
            return
        tier = self.subs.get_user_tier(self.username)
        names = {"free": "FREE (5 msgs/day)", "pro": "PRO", "builder": "BUILDER"}
        self.tier_label.setText(names.get(tier, tier.upper()))
        if tier == "builder":
            bal = self.subs.get_token_balance(self.username)
            self.token_label.setText(f"Tokens: {bal}")
            self.token_label.show()
        else:
            self.token_label.hide()

    def _upgrade(self, tier):
        if not self.subs:
            QMessageBox.warning(self, "Error", "Subscriptions not configured")
            return
        url = self.subs.create_checkout_link(self.username, tier=tier)
        if url:
            QMessageBox.information(
                self, "Payment",
                f"Payment page opened in your browser.\n\n"
                f"After payment, contact admin to activate your {tier.upper()} subscription."
            )
        else:
            QMessageBox.warning(
                self, "Error",
                "Could not create payment link. Check Square configuration."
            )

    def _buy_tokens(self):
        if not self.subs:
            return
        tier = self.subs.get_user_tier(self.username)
        if tier != "builder":
            QMessageBox.information(
                self, "Tokens",
                "Token purchases are available for Builder subscribers."
            )
            return
        from desktop_app.services.subscription_service import TOKEN_PACKS
        items = [f"{p['label']} — {p['price_display']}" for p in TOKEN_PACKS]
        choice, ok = QInputDialog.getItem(
            self, "Buy Tokens", "Select token pack:", items, editable=False
        )
        if not ok:
            return
        idx = items.index(choice)
        url = self.subs.create_checkout_link(self.username, token_pack_idx=idx)
        if url:
            QMessageBox.information(
                self, "Payment",
                "Payment page opened. Tokens will be added after admin confirms payment."
            )
