"""
Main Application Window for JARVIS.
Integrates top header with Orb, multi-tab layout, and bottom telemetry status bar.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QStatusBar, QMessageBox,
    QPushButton, QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
from datetime import datetime
from typing import Optional

from jarvis.ui.styles import DARK_THEME_QSS
from jarvis.ui.orb_widget import OrbWidget
from jarvis.ui.chat_widget import ChatWidget
from jarvis.ui.memory_widget import MemoryWidget
from jarvis.ui.tasks_widget import TasksWidget
from jarvis.ui.tools_widget import ToolsWidget
from jarvis.ui.settings_widget import SettingsWidget
from jarvis.ui.companion_widget import CompanionWidget
from jarvis.core.events import bus, AssistantState
from jarvis.core.config import active_config
from jarvis.memory.memory_service import memory_service
from jarvis.speech.wake_word import wake_word_service
from jarvis.speech.tts_engine import tts_engine
from jarvis.startup.greeting_service import greeting_service


class MainWindow(QMainWindow):
    def __init__(
        self,
        is_startup_launch: bool = False,
        start_as_companion: bool = False,
        silent_greeting: bool = False
    ):
        super().__init__()
        self.is_startup_launch = is_startup_launch
        self.start_as_companion = start_as_companion
        self.silent_greeting = silent_greeting
        self.setWindowTitle("JARVIS — Personal AI Friend & Companion")
        self.resize(1020, 760)
        self.setStyleSheet(DARK_THEME_QSS)

        self._init_ui()
        self._setup_event_listeners()
        self._setup_system_tray()

        # Update time timer (every second)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        # Handle startup greeting
        if not self.silent_greeting:
            QTimer.singleShot(1500, self._check_startup_greeting)

        # Start wake word listener if configured
        if active_config.speech.wake_word_enabled:
            wake_word_service.on_wake_callback = self._on_wake_word_triggered
            wake_word_service.start()

        if self.start_as_companion:
            QTimer.singleShot(100, self._show_companion_mode)

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # 1. Top Header Bar
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 10px;
                padding: 6px 12px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)

        # Left: Orb + Title
        self.orb = OrbWidget()
        header_layout.addWidget(self.orb)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        app_title = QLabel("J.A.R.V.I.S.")
        app_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #00D2FF; letter-spacing: 2px;")
        sub_title = QLabel(f"Personal Companion for {active_config.user.user_name}")
        sub_title.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: 500;")
        title_vbox.addWidget(app_title)
        title_vbox.addWidget(sub_title)
        header_layout.addLayout(title_vbox)

        header_layout.addStretch()

        # Center: State Status Pill
        self.state_pill = QLabel("🟢 IDLE")
        self.state_pill.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #38BDF8;
                border: 1px solid #1E293B;
                border-radius: 14px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        header_layout.addWidget(self.state_pill)

        # Companion Mode Toggle Button
        self.companion_btn = QPushButton("🗖 Companion")
        self.companion_btn.setToolTip("Switch to compact floating desktop companion")
        self.companion_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #00D2FF;
                border: 1px solid #00D2FF;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.companion_btn.clicked.connect(self._show_companion_mode)
        header_layout.addWidget(self.companion_btn)

        header_layout.addStretch()

        # Right: Clock & Date
        clock_vbox = QVBoxLayout()
        clock_vbox.setSpacing(2)
        clock_vbox.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #F8FAFC;")
        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-size: 11px; color: #94A3B8;")
        clock_vbox.addWidget(self.time_label)
        clock_vbox.addWidget(self.date_label)
        header_layout.addLayout(clock_vbox)

        main_layout.addWidget(header)

        # 2. Tabs
        self.tabs = QTabWidget()
        self.chat_tab = ChatWidget()
        self.memory_tab = MemoryWidget()
        self.tasks_tab = TasksWidget()
        self.tools_tab = ToolsWidget()
        self.settings_tab = SettingsWidget()

        # Initialize Companion Widget
        self.companion_widget = CompanionWidget(main_window=self)

        self.tabs.addTab(self.chat_tab, "💬 Conversation")
        self.tabs.addTab(self.memory_tab, "🧠 Memory & Profile")
        self.tabs.addTab(self.tasks_tab, "📋 Tasks & Reminders")
        self.tabs.addTab(self.tools_tab, "⚡ Tools & Audit")
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")

        main_layout.addWidget(self.tabs, stretch=1)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0B0F19;
                color: #64748B;
                border-top: 1px solid #1E293B;
                font-size: 11px;
            }
        """)
        self.setStatusBar(self.status_bar)

        self.llm_status = QLabel(f"Brain: {active_config.llm.provider.capitalize()}")
        self.voice_status = QLabel(f"Voice: {active_config.speech.edge_voice.split('-')[-1]}")
        self.mem_status = QLabel("Memories: 0")

        self.status_bar.addWidget(self.llm_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.voice_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.mem_status)

        self._update_clock()
        self._update_memory_count()

    def _setup_event_listeners(self):
        bus.state_changed.connect(self._on_state_changed)
        bus.error_occurred.connect(self._on_error)
        bus.memory_changed.connect(self._update_memory_count)
        bus.navigation_requested.connect(self._on_navigation_requested)
        bus.action_confirmation_requested.connect(self._on_action_confirmation_requested)

    @Slot(str)
    def _on_navigation_requested(self, tab_name: str):
        tab_map = {
            "conversation": 0, "chat": 0,
            "memory": 1, "profile": 1,
            "tasks": 2, "reminders": 2,
            "tools": 3, "audit": 3,
            "settings": 4, "config": 4
        }
        idx = tab_map.get(tab_name.lower().strip(), 0)
        self.tabs.setCurrentIndex(idx)

    @Slot(str, str)
    def _on_action_confirmation_requested(self, action_name: str, prompt: str):
        reply = QMessageBox.question(
            self,
            "Security Confirmation Required",
            f"JARVIS requests your permission for action: '{action_name}'.\n\n{prompt}\n\nDo you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from jarvis.tools.action_registry import action_registry
            res = action_registry.execute(action_name)
            if res["success"]:
                msg = res["result"].get("message", "Action completed successfully.")
                bus.message_received.emit("jarvis", f"Confirmed Rehan bhai! {msg}")
            else:
                bus.message_received.emit("jarvis", f"Action failed: {res.get('error')}")
        else:
            bus.message_received.emit("jarvis", f"Action '{action_name}' cancelled by user.")

    def _update_clock(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%I:%M:%S %p"))
        self.date_label.setText(now.strftime("%a, %d %b %Y"))

    def _update_memory_count(self):
        try:
            mems = memory_service.list_memories()
            self.mem_status.setText(f"Memories: {len(mems)} saved")
        except Exception:
            pass

    def _setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        px = QPixmap(32, 32)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#00D2FF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.end()
        self.tray_icon.setIcon(QIcon(px))
        self.tray_icon.setToolTip("JARVIS — Personal AI Friend & Companion")

        tray_menu = QMenu()
        act_companion = tray_menu.addAction("🗖 Show Companion")
        act_companion.triggered.connect(self._show_companion_mode)

        act_dashboard = tray_menu.addAction("⛶ Open Full Dashboard")
        act_dashboard.triggered.connect(self._show_dashboard)

        tray_menu.addSeparator()

        act_hands_free = tray_menu.addAction("🔄 Toggle Hands-Free Mode")
        act_hands_free.triggered.connect(self._toggle_hands_free)

        act_mute = tray_menu.addAction("🔇 Toggle Mic Mute")
        act_mute.triggered.connect(self.chat_tab._toggle_mute)

        tray_menu.addSeparator()

        act_exit = tray_menu.addAction("✕ Exit JARVIS")
        act_exit.triggered.connect(self._quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _show_companion_mode(self):
        self.hide()
        if hasattr(self, "companion_widget"):
            self.companion_widget.show()
            self.companion_widget.raise_()
            self.companion_widget.activateWindow()
            try:
                import win32gui, win32con
                hwnd = int(self.companion_widget.winId())
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

    def _show_dashboard(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        try:
            import win32gui, win32con
            hwnd = int(self.winId())
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _toggle_hands_free(self):
        from jarvis.speech.stt_engine import stt_engine
        is_cont = active_config.speech.listening_mode == "continuous"
        new_mode = "push_to_talk" if is_cont else "continuous"
        stt_engine.set_listening_mode(new_mode, callback=self.chat_tab.send_prompt if new_mode == "continuous" else None)
        bus.listening_mode_changed.emit(new_mode)

    def _quit_application(self):
        wake_word_service.stop()
        from jarvis.speech.stt_engine import stt_engine
        stt_engine.stop_continuous_listening()
        tts_engine.stop()
        self.tray_icon.hide()
        if hasattr(self, "companion_widget"):
            self.companion_widget.close()
        QApplication.quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self._show_companion_mode()
            else:
                self._show_dashboard()

    def closeEvent(self, event):
        # When closing main window, switch to companion mode if tray is running
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self._show_companion_mode()
        else:
            self._quit_application()
            event.accept()

    @Slot(str)
    def _on_state_changed(self, state: str):
        if state == AssistantState.LISTENING:
            self.state_pill.setText("🎙️ LISTENING...")
            self.state_pill.setStyleSheet("background-color: #064E3B; color: #34D399; border: 1px solid #059669; border-radius: 14px; padding: 6px 16px; font-weight: bold;")
        elif state == AssistantState.THINKING:
            self.state_pill.setText("⚡ THINKING...")
            self.state_pill.setStyleSheet("background-color: #4C1D95; color: #C084FC; border: 1px solid #7C3AED; border-radius: 14px; padding: 6px 16px; font-weight: bold;")
        elif state == AssistantState.EXECUTING:
            self.state_pill.setText("⚙️ EXECUTING...")
            self.state_pill.setStyleSheet("background-color: #78350F; color: #FCD34D; border: 1px solid #D97706; border-radius: 14px; padding: 6px 16px; font-weight: bold;")
        elif state == AssistantState.SPEAKING:
            self.state_pill.setText("🔊 SPEAKING...")
            self.state_pill.setStyleSheet("background-color: #0C4A6E; color: #38BDF8; border: 1px solid #0284C7; border-radius: 14px; padding: 6px 16px; font-weight: bold;")
        elif state == AssistantState.ERROR:
            self.state_pill.setText("🔴 NOTICE")
            self.state_pill.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; border: 1px solid #DC2626; border-radius: 14px; padding: 6px 16px; font-weight: bold;")
        else:
            self.state_pill.setText("🟢 IDLE")
            self.state_pill.setStyleSheet("background-color: #111827; color: #38BDF8; border: 1px solid #1E293B; border-radius: 14px; padding: 6px 16px; font-weight: bold;")

    @Slot(str, str)
    def _on_error(self, title: str, details: str):
        QMessageBox.warning(self, title, details)

    def _on_wake_word_triggered(self, command_text: Optional[str] = None):
        """Wake word heard: execute command immediately or activate mic."""
        if command_text:
            self.chat_tab.send_prompt(command_text)
        else:
            tts_engine.speak("Ji Rehan bhai?")
            def _activate():
                import time
                time.sleep(1.0)
                self.chat_tab._toggle_mic()
            import threading
            threading.Thread(target=_activate, daemon=True).start()

    def _check_startup_greeting(self):
        """Check if startup greeting should play."""
        if self.is_startup_launch or greeting_service.should_play_greeting():
            greeting_service.deliver_startup_greeting()
            self._update_memory_count()
