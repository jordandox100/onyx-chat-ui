"""Login/Register dialog — shown on app startup."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QWidget,
)
from PySide6.QtCore import Qt

from desktop_app.ui.styles import (
    BG_DEEP, BG_BASE, BG_SURFACE, BORDER, TEXT_PRI, TEXT_SEC,
    TEXT_MUTED, ACCENT, DANGER,
)

DIALOG_SS = f"""
QDialog {{
    background: {BG_DEEP};
}}
QLabel {{
    color: {TEXT_PRI};
}}
QLineEdit {{
    background: {BG_SURFACE};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 14px;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QPushButton#primary {{
    background: {ACCENT};
    color: {BG_DEEP};
    border: none;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    opacity: 0.9;
}}
QPushButton#secondary {{
    background: transparent;
    color: {TEXT_SEC};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 10px;
    font-size: 13px;
}}
QPushButton#secondary:hover {{
    border-color: {TEXT_SEC};
}}
"""


class LoginDialog(QDialog):
    """Login or register. Returns username on accept."""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth = auth_service
        self._username = ""
        self.setWindowTitle("ONYX — Login")
        self.setFixedSize(400, 420)
        self.setStyleSheet(DIALOG_SS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.init_ui()

    @property
    def username(self) -> str:
        return self._username

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(12)

        brand = QLabel("ONYX")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(
            f"font-size:32px; font-weight:800; color:{ACCENT};"
            f" letter-spacing:6px; padding:10px;"
        )
        root.addWidget(brand)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_page())
        self.stack.addWidget(self._build_register_page())
        root.addWidget(self.stack)

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Username")
        lay.addWidget(self.login_user)

        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Password")
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pass.returnPressed.connect(self._do_login)
        lay.addWidget(self.login_pass)

        self.login_error = QLabel("")
        self.login_error.setStyleSheet(f"color:{DANGER}; font-size:12px;")
        self.login_error.setWordWrap(True)
        lay.addWidget(self.login_error)

        btn = QPushButton("Login")
        btn.setObjectName("primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._do_login)
        lay.addWidget(btn)

        switch = QPushButton("Create Account")
        switch.setObjectName("secondary")
        switch.setCursor(Qt.CursorShape.PointingHandCursor)
        switch.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        lay.addWidget(switch)

        return page

    def _build_register_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(10)

        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("Username (3+ chars)")
        lay.addWidget(self.reg_user)

        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Password (6+ chars)")
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.reg_pass)

        self.reg_pass2 = QLineEdit()
        self.reg_pass2.setPlaceholderText("Confirm Password")
        self.reg_pass2.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pass2.returnPressed.connect(self._do_register)
        lay.addWidget(self.reg_pass2)

        self.reg_error = QLabel("")
        self.reg_error.setStyleSheet(f"color:{DANGER}; font-size:12px;")
        self.reg_error.setWordWrap(True)
        lay.addWidget(self.reg_error)

        btn = QPushButton("Register")
        btn.setObjectName("primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._do_register)
        lay.addWidget(btn)

        switch = QPushButton("Back to Login")
        switch.setObjectName("secondary")
        switch.setCursor(Qt.CursorShape.PointingHandCursor)
        switch.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        lay.addWidget(switch)

        return page

    def _do_login(self):
        u = self.login_user.text().strip()
        p = self.login_pass.text()
        ok, msg = self.auth.login(u, p)
        if ok:
            self._username = u
            self.accept()
        else:
            self.login_error.setText(msg)

    def _do_register(self):
        u = self.reg_user.text().strip()
        p = self.reg_pass.text()
        p2 = self.reg_pass2.text()
        if p != p2:
            self.reg_error.setText("Passwords don't match")
            return
        ok, msg = self.auth.register(u, p)
        if ok:
            self.reg_error.setStyleSheet(f"color:{ACCENT}; font-size:12px;")
            self.reg_error.setText("Account created! Logging in...")
            ok2, msg2 = self.auth.login(u, p)
            if ok2:
                self._username = u
                self.accept()
            else:
                self.reg_error.setText(msg2)
        else:
            self.reg_error.setText(msg)
