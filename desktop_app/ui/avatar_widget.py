"""Animated robot avatar widget — head bobs and mouth moves while speaking"""
import math
import time

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath


ACCENT = QColor("#00d4ff")
ACCENT_DIM = QColor("#0099bb")
ACCENT_GLOW = QColor(0, 212, 255, 40)
HEAD_DARK = QColor("#0c1017")
HEAD_MID = QColor("#121822")
FACE_PLATE = QColor("#161e2c")
BORDER_CLR = QColor("#1c2638")
EYE_OFF = QColor("#1c2638")
MOUTH_OFF = QColor("#1c2638")


class RobotAvatar(QWidget):
    def __init__(self, size=56, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._speaking = False
        self._mouth_phase = 0.0
        self._head_tilt = 0.0
        self._blink = False
        self._eye_glow = 0.6
        self._t0 = time.time()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    @property
    def speaking(self):
        return self._speaking

    @speaking.setter
    def speaking(self, val: bool):
        self._speaking = val

    def _tick(self):
        t = time.time() - self._t0
        if self._speaking:
            self._mouth_phase = abs(math.sin(t * 7.5)) * 0.85
            self._head_tilt = math.sin(t * 1.8) * 4.0
            self._eye_glow = 0.7 + 0.3 * abs(math.sin(t * 3))
        else:
            self._mouth_phase = max(0, self._mouth_phase - 0.08)
            self._head_tilt *= 0.9
            self._eye_glow = 0.45 + 0.15 * math.sin(t * 0.8)

        self._blink = (int(t * 10) % 50) < 2
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        p.translate(cx, cy)
        p.rotate(self._head_tilt)
        p.translate(-cx, -cy)

        # ── Outer glow ──
        if self._speaking:
            glow = QColor(0, 212, 255, int(25 * self._eye_glow))
            p.setBrush(QBrush(glow))
            p.setPen(QPen(Qt.PenStyle.NoPen))
            p.drawRoundedRect(3, 3, w - 6, h - 6, 16, 16)

        # ── Antenna ──
        p.setPen(QPen(BORDER_CLR, 2))
        p.drawLine(int(cx), 8, int(cx), 2)
        ant_glow = QColor(0, 212, 255, int(200 * self._eye_glow))
        p.setBrush(QBrush(ant_glow))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        p.drawEllipse(QPointF(cx, 2), 3, 3)

        # ── Head shell ──
        p.setBrush(QBrush(HEAD_DARK))
        p.setPen(QPen(ACCENT_DIM, 1.5))
        p.drawRoundedRect(6, 8, w - 12, h - 14, 14, 14)

        # ── Face plate ──
        p.setBrush(QBrush(FACE_PLATE))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        p.drawRoundedRect(10, 14, w - 20, h - 24, 10, 10)

        # ── Eyes ──
        eye_h = 3 if self._blink else 9
        eye_y = 22
        eye_color = QColor(0, 212, 255, int(255 * self._eye_glow))
        p.setBrush(QBrush(eye_color))
        # Left eye
        p.drawRoundedRect(15, eye_y, 9, eye_h, 3, 3)
        # Right eye
        p.drawRoundedRect(w - 24, eye_y, 9, eye_h, 3, 3)

        # ── Eye scanline detail ──
        if not self._blink:
            scan = QColor(0, 180, 230, 80)
            p.setPen(QPen(scan, 0.5))
            for dy in range(0, eye_h, 2):
                p.drawLine(15, eye_y + dy, 24, eye_y + dy)
                p.drawLine(w - 24, eye_y + dy, w - 15, eye_y + dy)
            p.setPen(QPen(Qt.PenStyle.NoPen))

        # ── Mouth ──
        mouth_base = 2
        mouth_open = max(mouth_base, int(self._mouth_phase * 12))
        mouth_y = 37
        mouth_w = 20
        mx = int(cx - mouth_w / 2)

        if self._speaking and self._mouth_phase > 0.1:
            mouth_color = QColor(0, 212, 255, int(180 * self._mouth_phase))
        else:
            mouth_color = MOUTH_OFF
        p.setBrush(QBrush(mouth_color))
        p.drawRoundedRect(mx, mouth_y, mouth_w, mouth_open, 3, 3)

        # ── Chin detail lines ──
        p.setPen(QPen(BORDER_CLR, 0.5))
        detail_y = h - 10
        p.drawLine(14, detail_y, w - 14, detail_y)

        p.end()


# Need Qt import for PenStyle
from PySide6.QtCore import Qt
