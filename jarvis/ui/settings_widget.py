"""
Settings and Preferences Widget for JARVIS.
Allows configuring AI models, natural female neural voice,
listening modes (Push-to-Talk, Continuous, Wake-Word), Windows Startup,
and Privacy Controls with immediate persistence.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QGroupBox,
    QFormLayout, QMessageBox, QScrollArea
)
from jarvis.core.config import active_config
from jarvis.core.events import bus
from jarvis.speech.tts_engine import tts_engine
from jarvis.speech.stt_engine import stt_engine
from jarvis.speech.wake_word import wake_word_service
from jarvis.startup.windows_startup import startup_manager
from jarvis.startup.greeting_service import greeting_service
from jarvis.conversation.conversation_manager import conversation_manager


class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.load_values()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # Header
        title = QLabel("⚙️ Settings & Configuration")
        title.setObjectName("title_label")
        subtitle = QLabel("Configure AI models, natural female voice, startup behavior, and privacy.")
        subtitle.setObjectName("subtitle_label")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 1. User & Persona
        user_group = QGroupBox("User Profile & Addressing")
        user_form = QFormLayout(user_group)
        self.user_name_input = QLineEdit()
        self.address_combo = QComboBox()
        self.address_combo.addItems(["Rehan bhai", "bhai", "Rehan"])
        user_form.addRow("User Name:", self.user_name_input)
        user_form.addRow("Preferred Address:", self.address_combo)
        layout.addWidget(user_group)

        # 2. LLM Provider Configuration
        llm_group = QGroupBox("AI Brain & LLM Providers")
        llm_form = QFormLayout(llm_group)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["gemini", "openai", "offline"])
        llm_form.addRow("Active Provider:", self.provider_combo)

        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setPlaceholderText("Enter Google Gemini API Key...")
        llm_form.addRow("Gemini API Key:", self.gemini_key_input)

        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("Enter OpenAI / Groq / DeepSeek API Key...")
        llm_form.addRow("OpenAI / Groq Key:", self.openai_key_input)

        self.openai_base_input = QLineEdit()
        self.openai_base_input.setPlaceholderText("https://api.openai.com/v1 (or local Ollama: http://localhost:11434/v1)")
        llm_form.addRow("OpenAI Base URL:", self.openai_base_input)

        layout.addWidget(llm_group)

        # 3. Speech, Female Voice & Listening Mode
        speech_group = QGroupBox("Voice, Speech & Hands-Free Interaction")
        speech_form = QFormLayout(speech_group)

        self.stt_lang_combo = QComboBox()
        self.stt_lang_combo.addItems(["en-IN", "hi-IN", "en-US"])
        speech_form.addRow("Speech Recognition Language:", self.stt_lang_combo)

        self.listening_mode_combo = QComboBox()
        self.listening_mode_combo.addItems([
            "Push-to-Talk (Click to Speak)",
            "Continuous Conversation (Hands-Free)",
            "Wake-Word Activated ('Hey Jarvis')"
        ])
        speech_form.addRow("Listening Interaction Mode:", self.listening_mode_combo)

        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "hi-IN-SwaraNeural",    # Primary Natural Female Voice (Hindi/Hinglish)
            "en-IN-NeerjaNeural",   # Indian English Female Voice
            "en-US-JennyNeural",    # US English Female Voice
            "en-US-AriaNeural",     # Expressive US English Female Voice
            "hi-IN-MadhurNeural",   # Hindi Male Voice
            "en-IN-PrabhatNeural"   # Indian English Male Voice
        ])
        speech_form.addRow("Natural Voice (Female Default):", self.voice_combo)

        voice_btn_row = QHBoxLayout()
        test_voice_btn = QPushButton("🔊 Test Female Voice")
        test_voice_btn.clicked.connect(self._test_voice)
        voice_btn_row.addWidget(test_voice_btn)
        voice_btn_row.addStretch()
        speech_form.addRow("", voice_btn_row)

        self.wake_word_chk = QCheckBox("Enable background 'Hey Jarvis' wake-word monitoring")
        speech_form.addRow(self.wake_word_chk)

        layout.addWidget(speech_group)

        # 4. Windows Startup & Greetings
        startup_group = QGroupBox("Windows Startup & Session Greeting")
        startup_layout = QVBoxLayout(startup_group)

        self.startup_chk = QCheckBox("Launch JARVIS automatically on Windows sign-in")
        startup_layout.addWidget(self.startup_chk)

        self.greeting_chk = QCheckBox("Play warm female spoken greeting on laptop startup")
        startup_layout.addWidget(self.greeting_chk)

        self.mute_greeting_chk = QCheckBox("Mute greeting (Display text only, no audio)")
        startup_layout.addWidget(self.mute_greeting_chk)

        test_greet_btn = QPushButton("👋 Test Startup Greeting Now")
        test_greet_btn.clicked.connect(self._test_greeting)
        startup_layout.addWidget(test_greet_btn)

        layout.addWidget(startup_group)

        # 5. Privacy & Security
        privacy_group = QGroupBox("Privacy & Security")
        priv_layout = QVBoxLayout(privacy_group)
        self.privacy_chk = QCheckBox("Privacy Mode (Mutes microphone listening & disables external lookups)")
        priv_layout.addWidget(self.privacy_chk)
        layout.addWidget(privacy_group)

        # Save Button
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.setObjectName("primary_button")
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def load_values(self):
        self.user_name_input.setText(active_config.user.user_name)
        idx = self.address_combo.findText(active_config.user.preferred_address)
        if idx >= 0:
            self.address_combo.setCurrentIndex(idx)

        idx_prov = self.provider_combo.findText(active_config.llm.provider)
        if idx_prov >= 0:
            self.provider_combo.setCurrentIndex(idx_prov)

        self.gemini_key_input.setText(active_config.llm.gemini_api_key)
        self.openai_key_input.setText(active_config.llm.openai_api_key)
        self.openai_base_input.setText(active_config.llm.openai_base_url)

        idx_stt = self.stt_lang_combo.findText(active_config.speech.stt_language)
        if idx_stt >= 0:
            self.stt_lang_combo.setCurrentIndex(idx_stt)

        mode_map = {"push_to_talk": 0, "continuous": 1, "wake_word": 2}
        self.listening_mode_combo.setCurrentIndex(mode_map.get(active_config.speech.listening_mode, 0))

        idx_voice = self.voice_combo.findText(active_config.speech.edge_voice)
        if idx_voice >= 0:
            self.voice_combo.setCurrentIndex(idx_voice)

        self.wake_word_chk.setChecked(active_config.speech.wake_word_enabled)
        self.startup_chk.setChecked(startup_manager.is_startup_enabled())
        self.greeting_chk.setChecked(active_config.startup.play_startup_greeting)
        self.mute_greeting_chk.setChecked(active_config.startup.startup_greeting_muted)
        self.privacy_chk.setChecked(active_config.tools.privacy_mode)

    def _save_settings(self):
        active_config.user.user_name = self.user_name_input.text().strip() or "Rehan Raza"
        active_config.user.preferred_address = self.address_combo.currentText()

        active_config.llm.provider = self.provider_combo.currentText()
        active_config.llm.gemini_api_key = self.gemini_key_input.text().strip()
        active_config.llm.openai_api_key = self.openai_key_input.text().strip()
        active_config.llm.openai_base_url = self.openai_base_input.text().strip() or "https://api.openai.com/v1"

        active_config.speech.stt_language = self.stt_lang_combo.currentText()
        active_config.speech.edge_voice = self.voice_combo.currentText()
        tts_engine.edge_voice = active_config.speech.edge_voice

        # Listening mode
        mode_idx = self.listening_mode_combo.currentIndex()
        modes = ["push_to_talk", "continuous", "wake_word"]
        selected_mode = modes[mode_idx]
        active_config.speech.listening_mode = selected_mode
        stt_engine.set_listening_mode(selected_mode)
        bus.listening_mode_changed.emit(selected_mode)

        active_config.speech.wake_word_enabled = self.wake_word_chk.isChecked()

        # Update Windows Startup registry
        if self.startup_chk.isChecked():
            startup_manager.enable_startup()
            active_config.startup.launch_on_startup = True
        else:
            startup_manager.disable_startup()
            active_config.startup.launch_on_startup = False

        active_config.startup.play_startup_greeting = self.greeting_chk.isChecked()
        active_config.startup.startup_greeting_muted = self.mute_greeting_chk.isChecked()
        active_config.tools.privacy_mode = self.privacy_chk.isChecked()

        active_config.save()
        conversation_manager.refresh_llm()

        # Wake word service toggle
        if active_config.speech.wake_word_enabled:
            wake_word_service.start()
        else:
            wake_word_service.stop()

        QMessageBox.information(self, "Saved", "Configuration updated and saved successfully!")

    def _test_voice(self):
        voice = self.voice_combo.currentText()
        tts_engine.speak("Hello Rehan bhai! Ye mera natural female voice test hai. Sab ekdum first-class kaam kar raha hai.", voice=voice)

    def _test_greeting(self):
        greeting_service.deliver_startup_greeting(force=True)
