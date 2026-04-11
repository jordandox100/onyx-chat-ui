"""ONYX dark theme — modern, high-contrast, cyber-tech aesthetic"""

# ── Color tokens ──────────────────────────────────────────────
BG_DEEP     = "#080b10"
BG_BASE     = "#0c1017"
BG_SURFACE  = "#121822"
BG_RAISED   = "#1a2233"
BG_HOVER    = "#1f2b3d"
BORDER      = "#1c2638"
BORDER_LITE = "#253350"

TEXT_PRI    = "#e4e8ee"
TEXT_SEC    = "#8694a8"
TEXT_MUTED  = "#4e5d73"

ACCENT      = "#00d4ff"
ACCENT_DIM  = "#0099bb"
ACCENT_GLOW = "#00d4ff33"
USER_BG     = "#0d2847"
USER_BORDER = "#1a5fb4"
AGENT_BG    = "#121822"
AGENT_BORDER= "#00d4ff"
TOOL_BG     = "#0d1a12"
TOOL_BORDER = "#22c55e"
DANGER      = "#ef4444"
SUCCESS     = "#22c55e"

MAIN_STYLE = f"""
/* ── Global ────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {BG_DEEP};
    color: {TEXT_PRI};
    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', monospace;
    font-size: 13px;
}}

/* ── Sidebar ───────────────────────────────── */
#sidebar {{
    background-color: {BG_BASE};
    border-right: 1px solid {BORDER};
}}

/* ── Chat list ─────────────────────────────── */
QListWidget {{
    background-color: {BG_BASE};
    border: none;
    outline: none;
    padding: 6px;
}}
QListWidget::item {{
    background-color: transparent;
    color: {TEXT_SEC};
    padding: 10px 14px;
    border-radius: 6px;
    margin: 1px 0;
}}
QListWidget::item:hover {{
    background-color: {BG_RAISED};
    color: {TEXT_PRI};
}}
QListWidget::item:selected {{
    background-color: {BG_HOVER};
    color: #ffffff;
    border-left: 3px solid {ACCENT};
}}

/* ── Buttons ───────────────────────────────── */
QPushButton {{
    background-color: {BG_RAISED};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {BORDER_LITE};
}}
QPushButton:pressed {{
    background-color: {BG_SURFACE};
}}
QPushButton:disabled {{
    background-color: {BG_BASE};
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}

/* Primary */
QPushButton#primaryButton {{
    background-color: {ACCENT};
    color: #000000;
    border: none;
    font-weight: 700;
    letter-spacing: 0.5px;
}}
QPushButton#primaryButton:hover {{
    background-color: #33ddff;
}}
QPushButton#primaryButton:pressed {{
    background-color: {ACCENT_DIM};
}}

/* Stop agent button */
QPushButton#stopButton {{
    background-color: {DANGER};
    color: #ffffff;
    border: none;
    font-weight: 700;
    letter-spacing: 0.5px;
    border-radius: 6px;
    padding: 8px 16px;
}}
QPushButton#stopButton:hover {{
    background-color: #f87171;
}}
QPushButton#stopButton:pressed {{
    background-color: #dc2626;
}}

/* Compact toggle */
QPushButton#compactToggle {{
    background-color: transparent;
    color: {TEXT_SEC};
    border: none;
    font-size: 18px;
    padding: 4px 8px;
    min-width: 28px;
    max-width: 28px;
}}
QPushButton#compactToggle:hover {{
    color: {ACCENT};
}}

/* Voice */
QPushButton#voiceButton {{
    background-color: {BG_RAISED};
    border: 2px solid {BORDER};
    border-radius: 20px;
    min-width: 40px; max-width: 40px;
    min-height: 40px; max-height: 40px;
    font-size: 16px;
    color: {TEXT_SEC};
}}
QPushButton#voiceButton:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton#voiceButtonRecording {{
    background-color: {DANGER};
    border: 2px solid {DANGER};
    border-radius: 20px;
    min-width: 40px; max-width: 40px;
    min-height: 40px; max-height: 40px;
    color: #ffffff;
}}

/* Attach */
QPushButton#attachButton {{
    background-color: transparent;
    border: none;
    color: {TEXT_MUTED};
    font-size: 16px;
    padding: 6px;
    min-width: 32px; max-width: 32px;
}}
QPushButton#attachButton:hover {{
    color: {ACCENT};
}}

/* ── Text input ────────────────────────────── */
QTextEdit, QLineEdit {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    selection-background-color: {ACCENT_DIM};
    font-size: 14px;
}}
QTextEdit:focus, QLineEdit:focus {{
    border-color: {ACCENT};
}}

/* ── Combo box ─────────────────────────────── */
QComboBox {{
    background-color: {BG_RAISED};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 140px;
    font-size: 12px;
}}
QComboBox:hover {{
    border-color: {BORDER_LITE};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_RAISED};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    selection-background-color: {BG_HOVER};
    outline: none;
    padding: 4px;
}}

/* ── Scrollbar ─────────────────────────────── */
QScrollBar:vertical {{
    background: {BG_DEEP};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BORDER_LITE};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 0;
}}

/* ── Chat area ─────────────────────────────── */
#chatArea {{
    background-color: {BG_DEEP};
    border: none;
}}

/* ── Slider ────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {BORDER};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: #33ddff;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_DIM};
    border-radius: 2px;
}}

/* ── Checkbox / Toggle ─────────────────────── */
QCheckBox {{
    color: {TEXT_SEC};
    spacing: 8px;
    font-size: 12px;
    background: transparent;
}}
QCheckBox:hover {{
    color: {TEXT_PRI};
}}
QCheckBox::indicator {{
    width: 34px;
    height: 18px;
    border-radius: 9px;
    background-color: {BG_RAISED};
    border: 1px solid {BORDER};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}

/* ── Labels ────────────────────────────────── */
QLabel {{
    color: {TEXT_PRI};
    background: transparent;
}}

/* ── Dialog ────────────────────────────────── */
QDialog, QInputDialog, QMessageBox {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRI};
}}

/* ── Menu ──────────────────────────────────── */
QMenu {{
    background-color: {BG_RAISED};
    color: {TEXT_PRI};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {BG_HOVER};
}}

/* ── Inspector panel ──────────────────────── */
#inspectorPanel {{
    background-color: {BG_DEEP};
    border-left: 1px solid {BORDER};
}}

#inspectorToggle {{
    background: transparent;
    color: {TEXT_SEC};
    border: none;
    font-size: 16px;
    padding: 4px 8px;
    min-width: 28px;
    max-width: 28px;
}}
#inspectorToggle:hover {{
    color: {ACCENT};
}}
"""

# ── HTML templates for chat messages ─────────────────────────
USER_MSG_HTML = """
<div style="margin:8px 48px 8px 120px; padding:12px 16px;
            background-color:{user_bg}; border:1px solid {user_border};
            border-radius:12px 12px 2px 12px;">
    <span style="color:{accent}; font-weight:700; font-size:11px;
                 text-transform:uppercase; letter-spacing:1px;">You</span><br>
    <span style="color:#e4e8ee; font-size:14px; line-height:1.5;">{text}</span>
</div>
""".replace("{user_bg}", USER_BG).replace("{user_border}", USER_BORDER).replace("{accent}", ACCENT)

AGENT_MSG_HTML = """
<div style="margin:8px 120px 8px 0; padding:12px 16px;
            background-color:{agent_bg}; border-left:3px solid {agent_border};
            border-radius:2px 12px 12px 12px;">
    <span style="color:{accent}; font-weight:700; font-size:11px;
                 text-transform:uppercase; letter-spacing:1px;">ONYX</span><br>
    <span style="color:#e4e8ee; font-size:14px; line-height:1.5;">{text}</span>
</div>
""".replace("{agent_bg}", AGENT_BG).replace("{agent_border}", AGENT_BORDER).replace("{accent}", ACCENT)

TOOL_MSG_HTML = """
<div style="margin:4px 120px 4px 24px; padding:8px 12px;
            background-color:{tool_bg}; border-left:3px solid {tool_border};
            border-radius:4px; font-family:monospace; font-size:12px;">
    <span style="color:{tool_border}; font-weight:700;">{tool_type}</span>
    <span style="color:#8694a8;"> {tool_cmd}</span><br>
    <pre style="color:#c8d0dc; margin:4px 0 0 0; white-space:pre-wrap;">{tool_result}</pre>
</div>
""".replace("{tool_bg}", TOOL_BG).replace("{tool_border}", TOOL_BORDER)

TYPING_INDICATOR_HTML = f"""
<div style="margin:8px 120px 8px 0; padding:12px 16px;
            background-color:{AGENT_BG}; border-left:3px solid {ACCENT_DIM};
            border-radius:2px 12px 12px 12px;">
    <span style="color:{ACCENT}; font-weight:700; font-size:11px;
                 text-transform:uppercase; letter-spacing:1px;">ONYX</span><br>
    <span style="color:{TEXT_MUTED};">thinking...</span>
</div>
"""

ATTACHMENT_HTML = """
<div style="margin:2px 48px 2px 120px; padding:6px 12px;
            background-color:#0f1825; border:1px solid #1c2638;
            border-radius:6px; font-size:12px;">
    <span style="color:#8694a8;">Attached:</span>
    <span style="color:#00d4ff;">{filename}</span>
    <span style="color:#4e5d73;">({size})</span>
</div>
"""

CODE_BLOCK_HTML = """
<table width="100%" cellspacing="0" cellpadding="0" style="margin:8px 0;">
<tr>
<td bgcolor="#121822" style="padding:4px 12px; border:1px solid #1c2638; border-bottom:none;">
<font color="#4e5d73" size="2">{lang}</font>
</td>
<td bgcolor="#121822" align="right" style="padding:4px 12px; border:1px solid #1c2638; border-bottom:none; border-left:none;">
<a href="copy://{key}" style="color:#00d4ff; font-size:11px; text-decoration:none;">Copy</a>
</td>
</tr>
<tr>
<td colspan="2" bgcolor="#0a0e14" style="padding:10px 14px; border:1px solid #1c2638; border-top:none;">
<pre style="color:#c8d0dc; font-size:12px; margin:0; white-space:pre-wrap; font-family:monospace;">{code}</pre>
</td>
</tr>
</table>
"""

LOAD_MORE_HTML = f"""
<div style="text-align:center; padding:10px; margin:4px 0;">
    <a href="loadmore://older" style="color:{ACCENT}; text-decoration:none;
       font-size:11px; padding:6px 20px; border:1px solid {BORDER};
       border-radius:4px; letter-spacing:1px;">
       LOAD OLDER MESSAGES
    </a>
</div>
"""

SUMMARY_BAR_HTML = f"""
<div style="text-align:center; padding:6px; margin:4px 40px;
            background:{BG_SURFACE}; border:1px solid {BORDER};
            border-radius:6px; font-size:11px; color:{TEXT_MUTED};">
    {{text}}
</div>
"""
