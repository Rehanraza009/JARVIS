"""
Speech-to-Text (STT) engine for JARVIS.
Supports Push-to-Talk, Continuous Hands-Free Conversation,
Mute control, and self-echo suppression.
"""

import time
import threading
from typing import Optional, Callable
from jarvis.core.config import active_config
from jarvis.core.logger import jarvis_logger
from jarvis.core.events import bus, AssistantState

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False


class STTEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer() if HAS_SR else None
        if self.recognizer:
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8

        self.is_listening = False
        self.is_muted = active_config.speech.is_mic_muted
        self.listening_mode = active_config.speech.listening_mode or "push_to_talk"
        self.language = active_config.speech.stt_language or "en-IN"

        self._continuous_running = False
        self._continuous_thread: Optional[threading.Thread] = None
        self._on_speech_callback: Optional[Callable[[str], None]] = None

        self._is_assistant_speaking = False
        self._is_processing_turn = False
        self._turn_finished_event = threading.Event()
        self._turn_finished_event.set()

        # Connect to event bus to guard against self-echo
        bus.speech_started.connect(self._on_assistant_speech_start)
        bus.speech_finished.connect(self._on_assistant_speech_end)
        bus.mic_mute_toggled.connect(self.set_muted)
        bus.state_changed.connect(self._on_bus_state_changed)

    def _on_assistant_speech_start(self, _):
        self._is_assistant_speaking = True
        self._is_processing_turn = True
        self._turn_finished_event.clear()

    def _on_assistant_speech_end(self):
        # Debounce to let room acoustic echo clear completely before resuming microphone
        def _clear():
            time.sleep(0.7)
            self._is_assistant_speaking = False
            self._is_processing_turn = False
            self._turn_finished_event.set()
        threading.Thread(target=_clear, daemon=True).start()

    def _on_bus_state_changed(self, state: str):
        if state == AssistantState.IDLE:
            # If idle and not speaking, ensure turn processing flag resets after brief delay
            if not self._is_assistant_speaking:
                def _release():
                    time.sleep(0.5)
                    if not self._is_assistant_speaking:
                        self._is_processing_turn = False
                        self._turn_finished_event.set()
                threading.Thread(target=_release, daemon=True).start()

    def set_muted(self, muted: bool):
        self.is_muted = muted
        active_config.speech.is_mic_muted = muted
        if muted:
            self._is_processing_turn = False
            self._turn_finished_event.set()
            self.is_listening = False
            bus.state_changed.emit(AssistantState.IDLE)
        jarvis_logger.info(f"Microphone mute state: {muted}")

    def set_listening_mode(self, mode: str, callback: Optional[Callable[[str], None]] = None):
        """Set listening mode: 'push_to_talk', 'continuous', or 'wake_word'."""
        self.listening_mode = mode
        active_config.speech.listening_mode = mode

        if callback:
            self._on_speech_callback = callback

        if mode == "continuous":
            self.start_continuous_listening(self._on_speech_callback)
        else:
            self.stop_continuous_listening()

        jarvis_logger.info(f"Listening mode changed to: {mode}")

    def is_available(self) -> bool:
        if not HAS_SR:
            return False
        try:
            mics = sr.Microphone.list_microphone_names()
            return len(mics) > 0
        except Exception:
            return False

    def listen_once_async(self, callback: Callable[[str], None]):
        """Listen for a single phrase in a background thread (Push-to-Talk)."""
        if not HAS_SR:
            bus.error_occurred.emit("Speech Error", "SpeechRecognition is not installed.")
            return

        if self.is_muted:
            jarvis_logger.info("Microphone is currently muted.")
            bus.state_changed.emit(AssistantState.IDLE)
            return

        threading.Thread(target=self._listen_worker, args=(callback,), daemon=True).start()

    def _listen_worker(self, callback: Callable[[str], None]):
        if self._is_assistant_speaking or self.is_muted:
            bus.state_changed.emit(AssistantState.IDLE)
            return

        bus.state_changed.emit(AssistantState.LISTENING)
        self.is_listening = True

        try:
            with sr.Microphone() as source:
                jarvis_logger.info("Microphone active. Calibrating noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                jarvis_logger.info("Listening for voice...")
                audio = self.recognizer.listen(
                    source,
                    timeout=active_config.speech.listen_timeout_seconds,
                    phrase_time_limit=10
                )

            # Echo guard check before transcription
            if self._is_assistant_speaking or self.is_muted:
                self.is_listening = False
                bus.state_changed.emit(AssistantState.IDLE)
                return

            bus.state_changed.emit(AssistantState.THINKING)
            jarvis_logger.info("Transcribing speech...")

            text = ""
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
            except sr.UnknownValueError:
                fallback_lang = "hi-IN" if self.language == "en-IN" else "en-IN"
                try:
                    text = self.recognizer.recognize_google(audio, language=fallback_lang)
                except Exception:
                    text = ""

            self.is_listening = False
            if text:
                jarvis_logger.info(f"Transcribed speech: '{text}'")
                self._is_processing_turn = True
                self._turn_finished_event.clear()
                bus.speech_detected.emit(text)
                bus.transcript_updated.emit(text)
                callback(text)
            else:
                self._is_processing_turn = False
                self._turn_finished_event.set()
                bus.state_changed.emit(AssistantState.IDLE)
                jarvis_logger.info("No speech detected.")

        except sr.WaitTimeoutError:
            self.is_listening = False
            self._is_processing_turn = False
            self._turn_finished_event.set()
            bus.state_changed.emit(AssistantState.IDLE)
            jarvis_logger.info("Listening timed out.")
        except Exception as e:
            self.is_listening = False
            self._is_processing_turn = False
            self._turn_finished_event.set()
            bus.state_changed.emit(AssistantState.IDLE)
            jarvis_logger.error(f"Microphone error: {e}")
            bus.error_occurred.emit("Microphone Notice", f"Audio input issue: {e}")

    def start_continuous_listening(self, callback: Callable[[str], None]):
        """Activate hands-free continuous loop."""
        if not HAS_SR:
            return

        self._on_speech_callback = callback
        if self._continuous_running:
            return

        self._continuous_running = True
        self._continuous_thread = threading.Thread(target=self._continuous_loop, daemon=True)
        self._continuous_thread.start()
        jarvis_logger.info("Continuous hands-free conversation loop started.")

    def stop_continuous_listening(self):
        """Deactivate continuous listening."""
        self._continuous_running = False
        self._is_processing_turn = False
        self._turn_finished_event.set()
        self.is_listening = False
        bus.state_changed.emit(AssistantState.IDLE)
        jarvis_logger.info("Continuous conversation stopped.")

    def _continuous_loop(self):
        while self._continuous_running:
            # If muted or assistant is speaking or processing turn, pause and wait
            if self.is_muted or self._is_assistant_speaking or self._is_processing_turn:
                time.sleep(0.2)
                continue

            def _on_turn_transcribed(text: str):
                if text and self._on_speech_callback:
                    self._on_speech_callback(text)

            self._listen_worker(_on_turn_transcribed)

            # Wait while assistant is processing turn and speaking before next listen
            while self._continuous_running and (self._is_processing_turn or self._is_assistant_speaking):
                time.sleep(0.2)

            time.sleep(0.3)


stt_engine = STTEngine()
