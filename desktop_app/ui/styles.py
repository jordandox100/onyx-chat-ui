"""Modern dark theme styles for ONYX"""

MAIN_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
    color: #e0e0e0;
}

QWidget {
    background-color: #0a0a0a;
    color: #e0e0e0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
}

/* Sidebar */
#sidebar {
    background-color: #111111;
    border-right: 1px solid #252525;
}

/* Chat list */
QListWidget {
    background-color: #111111;
    border: none;
    outline: none;
    padding: 8px;
}

QListWidget::item {
    background-color: transparent;
    color: #b0b0b0;
    padding: 12px 16px;
    border-radius: 8px;
    margin: 2px 0;
}

QListWidget::item:hover {
    background-color: #1a1a1a;
    color: #e0e0e0;
}

QListWidget::item:selected {
    background-color: #2a2a2a;
    color: #ffffff;
}

/* Buttons */
QPushButton {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2a2a2a;
    border-color: #3a3a3a;
}

QPushButton:pressed {
    background-color: #252525;
}

QPushButton:disabled {
    background-color: #151515;
    color: #505050;
    border-color: #1a1a1a;
}

/* Primary button */
QPushButton#primaryButton {
    background-color: #4a9eff;
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background-color: #5aaeff;
}

QPushButton#primaryButton:pressed {
    background-color: #3a8eef;
}

/* Voice button */
QPushButton#voiceButton {
    background-color: #1e1e1e;
    border: 2px solid #2a2a2a;
    border-radius: 24px;
    padding: 12px;
    min-width: 48px;
    max-width: 48px;
    min-height: 48px;
    max-height: 48px;
}

QPushButton#voiceButton:hover {
    border-color: #4a9eff;
    background-color: #2a2a2a;
}

QPushButton#voiceButton:pressed {
    background-color: #4a9eff;
    border-color: #4a9eff;
}

/* Recording state */
QPushButton#voiceButtonRecording {
    background-color: #ff4444;
    border-color: #ff4444;
    animation: pulse 1.5s infinite;
}

/* Text input */
QTextEdit, QLineEdit {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 2px solid #2a2a2a;
    border-radius: 12px;
    padding: 12px 16px;
    selection-background-color: #4a9eff;
}

QTextEdit:focus, QLineEdit:focus {
    border-color: #4a4a4a;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #0a0a0a;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #2a2a2a;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3a3a3a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0a0a0a;
    height: 12px;
}

QScrollBar::handle:horizontal {
    background-color: #2a2a2a;
    border-radius: 6px;
    min-width: 30px;
}

/* Chat area */
#chatArea {
    background-color: #0a0a0a;
    border: none;
}

/* Message bubbles */
.userMessage {
    background-color: #4a9eff;
    color: #ffffff;
    border-radius: 16px;
    padding: 12px 16px;
    margin: 8px 0;
}

.assistantMessage {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border-radius: 16px;
    padding: 12px 16px;
    margin: 8px 0;
    border: 1px solid #252525;
}

/* Menu Bar */
QMenuBar {
    background-color: #111111;
    color: #e0e0e0;
    border-bottom: 1px solid #252525;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #1e1e1e;
}

QMenu {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #2a2a2a;
}

/* Dialog */
QDialog {
    background-color: #1a1a1a;
    color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

/* Input Dialog */
QInputDialog {
    background-color: #1a1a1a;
}
"""
