"""
Chat View Widget for JARVIS.
Handles message history bubbles with timestamps, hands-free continuous conversation,
mode selector, mic mute control, and speech interruption.
"""

import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QLineEdit, QPushButton, QLabel, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCursor
from jarvis.core.events import bus, AssistantState
from jarvis.core.config import active_config
from jarvis.conversation.conversation_manager import conversation_manager
from jarvis.speech.stt_engine import stt_engine
from jarvis.speech.tts_engine import tts_engine


class ChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

        # Connect event bus signals
        bus.message_received.connect(self._on_message_received)
        bus.state_changed.connect(self._on_state_changed)
        bus.speech_detected.connect(self._on_speech_detected)
        bus.listening_mode_changed.connect(self._on_listening_mode_changed)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 1. Message History Browser
        self.history_browser = QTextBrowser()
        self.history_browser.setOpenExternalLinks(True)
        self.history_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #0B0F19;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.history_browser, stretch=1)

        # 2. Control Bar (Mode Selector + Mute + Quick Chips)
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(8)

        # Mode label & combo
        ctrl_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "🎙️ Push-to-Talk",
            "🔄 Continuous Hands-Free",
            "⚡ Wake Word ('Hey Jarvis')"
        ])
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #111827;
                color: #38BDF8;
                border: 1px solid #1E293B;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        ctrl_layout.addWidget(self.mode_combo)

        # Mute Microphone Button
        self.mute_btn = QPushButton("🎙️ Mic Active")
        self.mute_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #34D399;
                border: 1px solid #059669;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        self.mute_btn.clicked.connect(self._toggle_mute)
        ctrl_layout.addWidget(self.mute_btn)

        ctrl_layout.addSpacing(12)

        # Quick Prompt Chips
        chips = [
            ("👋 Sun rahi ho?", "Jarvis, sun rahi ho?"),
            ("⚙️ Settings kholo", "Settings kholo"),
            ("🎯 Career Talk", "Career ko lekar tension hai, thoda guide karo."),
            ("🧠 My Memories", "What do you remember about me?"),
            ("📋 Pending Tasks", "Show my pending tasks")
        ]
        for label, prompt_text in chips:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #111827;
                    color: #94A3B8;
                    border: 1px solid #1E293B;
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: #00D2FF;
                    border-color: #00D2FF;
                }
            """)
            btn.clicked.connect(lambda _, p=prompt_text: self.send_prompt(p))
            ctrl_layout.addWidget(btn)

        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # 3. Input Controls Bar
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        # Mic / Push-to-Talk Button
        self.mic_btn = QPushButton("🎙️ Push-to-Talk")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #00D2FF;
                border: 1px solid #00D2FF;
                border-radius: 6px;
                padding: 10px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
        """)
        self.mic_btn.clicked.connect(self._toggle_mic)
        input_layout.addWidget(self.mic_btn)

        # Text Input Box
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message or command (e.g. 'settings kholo', 'Chrome kholo', 'career advice')...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00D2FF;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send_clicked)
        input_layout.addWidget(self.input_field, stretch=1)

        # Send Button
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("primary_button")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._on_send_clicked)
        input_layout.addWidget(self.send_btn)

        # Stop Audio / Interruption Button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setObjectName("stop_button")
        self.stop_btn.setFixedWidth(75)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._stop_audio)
        input_layout.addWidget(self.stop_btn)

        layout.addLayout(input_layout)

    def _on_mode_combo_changed(self, idx: int):
        if idx == 0:
            stt_engine.set_listening_mode("push_to_talk")
            self.mic_btn.setEnabled(True)
            self.mic_btn.setText("🎙️ Push-to-Talk")
        elif idx == 1:
            stt_engine.set_listening_mode("continuous", callback=self.send_prompt)
            self.mic_btn.setEnabled(False)
            self.mic_btn.setText("🔄 Continuous Active")
        elif idx == 2:
            stt_engine.set_listening_mode("wake_word")
            self.mic_btn.setEnabled(True)
            self.mic_btn.setText("⚡ Wake-Word Ready")

    @Slot(str)
    def _on_listening_mode_changed(self, mode: str):
        if mode == "continuous":
            self.mode_combo.setCurrentIndex(1)
        elif mode == "wake_word":
            self.mode_combo.setCurrentIndex(2)
        else:
            self.mode_combo.setCurrentIndex(0)

    def _toggle_mute(self):
        new_mute = not stt_engine.is_muted
        stt_engine.set_muted(new_mute)
        bus.mic_mute_toggled.emit(new_mute)
        if new_mute:
            self.mute_btn.setText("🔇 Muted")
            self.mute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #371B1B;
                    color: #F87171;
                    border: 1px solid #DC2626;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
            """)
        else:
            self.mute_btn.setText("🎙️ Mic Active")
            self.mute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #111827;
                    color: #34D399;
                    border: 1px solid #059669;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
            """)

    def send_prompt(self, text: str):
        self.input_field.setText(text)
        self._on_send_clicked()

    def _on_send_clicked(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.send_btn.setEnabled(False)

        # Process in worker thread so UI never freezes
        threading.Thread(target=self._process_in_thread, args=(text,), daemon=True).start()

    def _process_in_thread(self, text: str):
        response = conversation_manager.process_message(text)
        # Speak the response using natural female voice
        tts_engine.speak(response)
        self.send_btn.setEnabled(True)

    def _toggle_mic(self):
        tts_engine.stop()
        self.mic_btn.setText("🎙️ Listening...")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #065F46;
                color: #34D399;
                border: 1px solid #10B981;
                border-radius: 6px;
                padding: 10px 14px;
                font-weight: bold;
            }
        """)

        def _on_speech(transcribed: str):
            self.mic_btn.setText("🎙️ Push-to-Talk")
            self.mic_btn.setStyleSheet("")
            if transcribed:
                self.send_prompt(transcribed)

        stt_engine.listen_once_async(_on_speech)

    def _stop_audio(self):
        tts_engine.stop()
        self.stop_btn.setVisible(False)

    @Slot(str)
    def _on_speech_detected(self, text: str):
        self.input_field.setText(text)

    @Slot(str, str)
    def _on_message_received(self, sender: str, text: str):
        cursor = self.history_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        now_time = datetime.now().strftime("%I:%M %p")

        # Format HTML bubble with clear styling and timestamp
        if sender == "user":
            html = f"""
            <div style="margin: 10px 0; text-align: right;">
                <div style="display: inline-block; background-color: #1E293B; color: #F1F5F9; border: 1px solid #334155; border-radius: 12px 12px 2px 12px; padding: 10px 14px; max-width: 80%; text-align: left;">
                    <div style="font-size: 11px; font-weight: bold; color: #38BDF8; margin-bottom: 4px;">Rehan Raza</div>
                    <div>{text.replace('\n', '<br>')}</div>
                    <div style="font-size: 10px; color: #64748B; text-align: right; margin-top: 4px;">{now_time}</div>
                </div>
            </div>
            """
        else:
            formatted_text = text.replace('\n', '<br>')
            html = f"""
            <div style="margin: 10px 0; text-align: left;">
                <div style="display: inline-block; background-color: #111827; color: #F8FAFC; border: 1px solid #1E293B; border-left: 3px solid #00D2FF; border-radius: 2px 12px 12px 12px; padding: 12px 16px; max-width: 85%;">
                    <div style="font-size: 11px; font-weight: bold; color: #00D2FF; margin-bottom: 6px;">⚡ JARVIS (Female Companion)</div>
                    <div style="color: #E2E8F0;">{formatted_text}</div>
                    <div style="font-size: 10px; color: #64748B; text-align: right; margin-top: 6px;">{now_time}</div>
                </div>
            </div>
            """

        self.history_browser.append(html)
        self.history_browser.moveCursor(QTextCursor.MoveOperation.End)

    @Slot(str)
    def _on_state_changed(self, state: str):
        if state == AssistantState.SPEAKING:
            self.stop_btn.setVisible(True)
        elif state == AssistantState.IDLE:
            self.stop_btn.setVisible(False)
            if self.mode_combo.currentIndex() == 0:
                self.mic_btn.setText("🎙️ Push-to-Talk")
