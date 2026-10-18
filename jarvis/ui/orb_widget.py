"""
Animated AI Orb Widget for JARVIS.
A responsive, lightweight custom widget using QPainter for concentric glowing pulses,
rotating rings, and state-aware visual feedback.
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush, QConicalGradient
from PySide6.QtCore import Qt, QTimer, QRectF
from jarvis.core.events import AssistantState, bus


class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(110, 110)
        self.state = AssistantState.IDLE
        self.phase = 0.0
        self.pulse_val = 0.0

        # Animation timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(33)

        # Connect to event bus
        bus.state_changed.connect(self.set_state)

    def set_state(self, new_state: str):
        try:
            self.state = AssistantState(new_state)
        except ValueError:
            self.state = AssistantState.IDLE
        self.update()

    def _update_animation(self):
        self.phase = (self.phase + 0.05) % (2 * math.pi)
        self.pulse_val = (math.sin(self.phase * 2) + 1) / 2.0  # 0.0 to 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        max_radius = min(center_x, center_y) - 6

        # Choose color scheme according to state
        if self.state == AssistantState.LISTENING:
            primary_color = QColor("#10B981")    # Emerald green
            glow_color = QColor("#00F0FF")       # Bright cyan
            speed_mult = 2.0
        elif self.state == AssistantState.THINKING:
            primary_color = QColor("#8B5CF6")    # Purple
            glow_color = QColor("#EC4899")       # Hot pink
            speed_mult = 2.5
        elif self.state == AssistantState.SPEAKING:
            primary_color = QColor("#00D2FF")    # Electric blue
            glow_color = QColor("#6366F1")       # Indigo
            speed_mult = 2.2
        elif self.state == AssistantState.ERROR:
            primary_color = QColor("#F43F5E")    # Crimson
            glow_color = QColor("#FB923C")       # Orange
            speed_mult = 1.0
        else:  # IDLE
            primary_color = QColor("#00D2FF")    # Calm Cyan
            glow_color = QColor("#1E3A8A")       # Deep blue
            speed_mult = 1.0

        # 1. Outer dynamic pulsing ring
        outer_pulse = max_radius * (0.85 + 0.15 * self.pulse_val)
        glow_pen = QPen(primary_color.lighter(130), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(center_x - outer_pulse, center_y - outer_pulse, outer_pulse * 2, outer_pulse * 2))

        # 2. Rotating orbital arc
        angle = math.degrees(self.phase * speed_mult) % 360
        arc_pen = QPen(primary_color, 2.5)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        mid_r = max_radius * 0.72
        painter.drawArc(
            QRectF(center_x - mid_r, center_y - mid_r, mid_r * 2, mid_r * 2),
            int(angle * 16),
            int(120 * 16)
        )
        painter.drawArc(
            QRectF(center_x - mid_r, center_y - mid_r, mid_r * 2, mid_r * 2),
            int((angle + 180) * 16),
            int(100 * 16)
        )

        # 3. Core Radial Glowing Orb
        core_r = max_radius * (0.45 + 0.1 * self.pulse_val)
        gradient = QRadialGradient(center_x, center_y, core_r)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 240))
        gradient.setColorAt(0.4, primary_color)
        gradient.setColorAt(0.8, glow_color)
        gradient.setColorAt(1.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QRectF(center_x - core_r, center_y - core_r, core_r * 2, core_r * 2))

        painter.end()
