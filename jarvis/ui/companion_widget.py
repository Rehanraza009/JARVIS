"""
Compact Floating Desktop Companion for JARVIS.
Displays real-time assistant state, live recognized transcript,
active action, response snippet, microphone control, and dashboard opener.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, QPoint, Slot
from PySide6.QtGui import QMouseEvent, QFont, QColor
from jarvis.core.events import bus, AssistantState
from jarvis.core.config import active_config
from jarvis.speech.stt_engine import stt_engine
from jarvis.speech.tts_engine import tts_engine


class CompanionWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.main_window = main_window
        self.always_on_top = True
        self._drag_pos = QPoint()

        self.setFixedSize(390, 240)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._init_ui()
        self._setup_events()
        self._update_window_flags()
        self._position_bottom_right()

    def _init_ui(self):
        # Outer card frame
        card = QFrame(self)
        card.setGeometry(0, 0, self.width(), self.height())
        card.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 2px solid #00D2FF;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # 1. Header Bar: Status, Title, Always-On-Top, Dashboard, Minimize
        header = QHBoxLayout()
        header.setSpacing(6)

        self.online_dot = QLabel("🟢")
        self.online_dot.setStyleSheet("font-size: 11px; border: none; background: transparent;")
        header.addWidget(self.online_dot)

        title_label = QLabel("JARVIS COMPANION")
        title_label.setStyleSheet("font-size: 13px; font-weight: 800; color: #00D2FF; letter-spacing: 1px; border: none; background: transparent;")
        header.addWidget(title_label)

        header.addStretch()

        # Pin / Always on top toggle
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setToolTip("Toggle Always on Top")
        self.pin_btn.setFixedSize(26, 24)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.pin_btn.clicked.connect(self._toggle_always_on_top)
        header.addWidget(self.pin_btn)

        # Open Full Dashboard button
        self.dashboard_btn = QPushButton("⛶ Dashboard")
        self.dashboard_btn.setToolTip("Open Full JARVIS Dashboard")
        self.dashboard_btn.setFixedHeight(24)
        self.dashboard_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
                border-color: #00D2FF;
            }
        """)
        self.dashboard_btn.clicked.connect(self._open_full_dashboard)
        header.addWidget(self.dashboard_btn)

        # Hide / Close Companion button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #EF4444;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # 2. State Indicator Pill
        self.state_pill = QLabel("🟢 ONLINE / IDLE")
        self.state_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_pill.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #38BDF8;
                border: 1px solid #1E293B;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.state_pill)

        # 3. Dynamic Transcript & Action Display
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #090D16;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(3)

        self.transcript_label = QLabel("🎙️ Heard: Ready for voice command...")
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        info_layout.addWidget(self.transcript_label)

        self.action_label = QLabel("⚡ Action: None")
        self.action_label.setWordWrap(True)
        self.action_label.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: 600; border: none; background: transparent;")
        info_layout.addWidget(self.action_label)

        self.answer_label = QLabel("💬 JARVIS: Ready, Rehan bhai.")
        self.answer_label.setWordWrap(True)
        self.answer_label.setStyleSheet("color: #94A3B8; font-size: 10px; border: none; background: transparent;")
        info_layout.addWidget(self.answer_label)

        layout.addWidget(info_frame, stretch=1)

        # 4. Bottom Controls: Mic, Stop, Continuous Mode Toggle
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(8)

        self.mic_btn = QPushButton("🎙️ Listen")
        self.mic_btn.setFixedHeight(28)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #00D2FF;
                border: 1px solid #00D2FF;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.mic_btn.clicked.connect(self._on_mic_clicked)
        ctrl_layout.addWidget(self.mic_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFixedHeight(28)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #371B1B;
                color: #F87171;
                border: 1px solid #DC2626;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7F1D1D;
                color: #FFFFFF;
            }
        """)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        ctrl_layout.addWidget(self.stop_btn)

        self.continuous_btn = QPushButton("🔄 Hands-Free")
        self.continuous_btn.setFixedHeight(28)
        self.continuous_btn.setCheckable(True)
        is_cont = active_config.speech.listening_mode == "continuous"
        self.continuous_btn.setChecked(is_cont)
        self._update_continuous_btn_style(is_cont)
        self.continuous_btn.clicked.connect(self._toggle_continuous_mode)
        ctrl_layout.addWidget(self.continuous_btn)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

    def _setup_events(self):
        bus.state_changed.connect(self._on_state_changed)
        bus.speech_detected.connect(self._on_speech_detected)
        bus.transcript_updated.connect(self._on_transcript_updated)
        bus.action_started.connect(self._on_action_started)
        bus.action_finished.connect(self._on_action_finished)
        bus.message_received.connect(self._on_message_received)
        bus.mic_mute_toggled.connect(self._on_mic_mute_toggled)

    def _position_bottom_right(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.x() + geom.width() - self.width() - 24
            y = geom.y() + geom.height() - self.height() - 24
            self.move(x, y)

    def _update_window_flags(self):
        flags = Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.pin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {'#0284C7' if self.always_on_top else '#1E293B'};
                color: #FFFFFF;
                border: 1px solid #00D2FF;
                border-radius: 4px;
                font-size: 12px;
            }}
        """)
        self._update_window_flags()

    def _open_full_dashboard(self):
        if self.main_window:
            self.main_window.showNormal()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _on_mic_clicked(self):
        tts_engine.stop()
        if self.main_window and hasattr(self.main_window, "chat_tab"):
            self.main_window.chat_tab._toggle_mic()
        else:
            def _on_speech(text: str):
                if text:
                    from jarvis.conversation.conversation_manager import conversation_manager
                    res = conversation_manager.process_message(text)
                    tts_engine.speak(res)
            stt_engine.listen_once_async(_on_speech)

    def _on_stop_clicked(self):
        tts_engine.stop()
        stt_engine.stop_continuous_listening()
        self.continuous_btn.setChecked(False)
        self._update_continuous_btn_style(False)

    def _toggle_continuous_mode(self):
        enabled = self.continuous_btn.isChecked()
        self._update_continuous_btn_style(enabled)
        if enabled:
            cb = self.main_window.chat_tab.send_prompt if self.main_window and hasattr(self.main_window, "chat_tab") else None
            stt_engine.set_listening_mode("continuous", callback=cb)
            bus.listening_mode_changed.emit("continuous")
        else:
            stt_engine.set_listening_mode("push_to_talk")
            bus.listening_mode_changed.emit("push_to_talk")

    def _update_continuous_btn_style(self, active: bool):
        if active:
            self.continuous_btn.setStyleSheet("""
                QPushButton {
                    background-color: #064E3B;
                    color: #34D399;
                    border: 1px solid #059669;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            self.continuous_btn.setText("🔄 Hands-Free ON")
        else:
            self.continuous_btn.setStyleSheet("""
                QPushButton {
                    background-color: #111827;
                    color: #94A3B8;
                    border: 1px solid #1E293B;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
            """)
            self.continuous_btn.setText("🔄 Hands-Free OFF")

    @Slot(str)
    def _on_state_changed(self, state: str):
        if state == AssistantState.LISTENING:
            self.state_pill.setText("🎙️ LISTENING...")
            self.state_pill.setStyleSheet("background-color: #064E3B; color: #34D399; border: 1px solid #059669; border-radius: 10px; padding: 4px 10px; font-weight: bold; font-size: 11px;")
        elif state == AssistantState.THINKING:
            self.state_pill.setText("⚡ THINKING...")
            self.state_pill.setStyleSheet("background-color: #4C1D95; color: #C084FC; border: 1px solid #7C3AED; border-radius: 10px; padding: 4px 10px; font-weight: bold; font-size: 11px;")
        elif state == AssistantState.EXECUTING:
            self.state_pill.setText("⚙️ EXECUTING ACTION...")
            self.state_pill.setStyleSheet("background-color: #78350F; color: #FCD34D; border: 1px solid #D97706; border-radius: 10px; padding: 4px 10px; font-weight: bold; font-size: 11px;")
        elif state == AssistantState.SPEAKING:
            self.state_pill.setText("🔊 SPEAKING...")
            self.state_pill.setStyleSheet("background-color: #0C4A6E; color: #38BDF8; border: 1px solid #0284C7; border-radius: 10px; padding: 4px 10px; font-weight: bold; font-size: 11px;")
        elif state == AssistantState.ERROR:
            self.state_pill.setText("🔴 NOTICE")
            self.state_pill.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; border: 1px solid #DC2626; border-radius: 10px; padding: 4px 10px; font-weight: bold; font-size: 11px;")
        else:
            self.state_pill.setText("🟢 ONLINE / IDLE")
            self.state_pill.setStyleSheet("background-color: #111827; color: #38BDF8; border: 1px solid #1E293B; border-radius: 10px; padding: 4px 10px; font-weight: bold; font-size: 11px;")

    @Slot(str)
    def _on_speech_detected(self, text: str):
        self.transcript_label.setText(f"🎙️ Heard: \"{text[:45]}\"")

    @Slot(str)
    def _on_transcript_updated(self, text: str):
        self.transcript_label.setText(f"🎙️ Heard: \"{text[:45]}\"")

    @Slot(str, str)
    def _on_action_started(self, action_name: str, args_str: str):
        self.action_label.setText(f"⚙️ Running: {action_name}")

    @Slot(str, bool, str)
    def _on_action_finished(self, action_name: str, success: bool, message: str):
        status_icon = "✓" if success else "✗"
        self.action_label.setText(f"⚡ Action [{status_icon}]: {action_name}")

    @Slot(str, str)
    def _on_message_received(self, sender: str, text: str):
        if sender == "jarvis":
            snippet = text.replace('\n', ' ')[:65]
            if len(text) > 65:
                snippet += "..."
            self.answer_label.setText(f"💬 JARVIS: {snippet}")

    @Slot(bool)
    def _on_mic_mute_toggled(self, muted: bool):
        if muted:
            self.mic_btn.setText("🔇 Muted")
            self.mic_btn.setStyleSheet("background-color: #371B1B; color: #F87171; border: 1px solid #DC2626; border-radius: 6px; padding: 4px 10px; font-size: 11px;")
        else:
            self.mic_btn.setText("🎙️ Listen")
            self.mic_btn.setStyleSheet("background-color: #1E293B; color: #00D2FF; border: 1px solid #00D2FF; border-radius: 6px; padding: 4px 10px; font-size: 11px;")

    # Window dragging handlers
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
