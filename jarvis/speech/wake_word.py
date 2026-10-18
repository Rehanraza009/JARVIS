import re
import threading
import time
from typing import Optional, Callable
from jarvis.core.config import active_config
from jarvis.core.logger import jarvis_logger
from jarvis.core.events import bus

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False


class WakeWordListener:
    def __init__(self, on_wake_callback: Optional[Callable[[Optional[str]], None]] = None):
        self.on_wake_callback = on_wake_callback
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.recognizer = sr.Recognizer() if HAS_SR else None
        if self.recognizer:
            self.recognizer.energy_threshold = 350
            self.recognizer.dynamic_energy_threshold = True

    def start(self):
        """Start background wake word monitoring thread."""
        if not HAS_SR or not active_config.speech.wake_word_enabled:
            return

        if self.is_running:
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        jarvis_logger.info("Wake word listener background monitor started.")

    def stop(self):
        """Stop background wake word monitoring."""
        self.is_running = False
        jarvis_logger.info("Wake word listener stopped.")

    def _monitor_loop(self):
        wake_phrases = [w.lower() for w in active_config.speech.wake_words]
        wake_phrases.extend(["hey jarvis", "jarvis", "jarvis bhai", "sun raha hai", "sun rahi ho", "jarvis sun rahi ho"])

        while self.is_running:
            # Skip if microphone is muted or assistant is speaking or processing turn
            from jarvis.speech.audio_player import audio_player
            from jarvis.speech.stt_engine import stt_engine
            if active_config.speech.is_mic_muted or audio_player.is_playing or stt_engine.is_listening or stt_engine._is_processing_turn:
                time.sleep(0.3)
                continue

            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)

                try:
                    phrase = self.recognizer.recognize_google(audio).lower().strip()
                    jarvis_logger.info(f"[WakeWord Check] Heard: '{phrase}'")

                    matched_wake = None
                    for w in wake_phrases:
                        if w in phrase:
                            matched_wake = w
                            break

                    if matched_wake:
                        jarvis_logger.info(f"Wake word '{matched_wake}' triggered from phrase: '{phrase}'")
                        remainder = re.sub(rf"^.*?{re.escape(matched_wake)}\s*,?\s*", "", phrase).strip()
                        bus.speech_detected.emit(phrase)
                        bus.transcript_updated.emit(phrase)

                        if self.on_wake_callback:
                            self.on_wake_callback(remainder if remainder else None)
                        time.sleep(1.0)

                except (sr.UnknownValueError, sr.WaitTimeoutError):
                    pass
                except Exception as e:
                    jarvis_logger.debug(f"Wake word recognition cycle exception: {e}")

            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                jarvis_logger.warning(f"Wake word loop mic error: {e}")
                time.sleep(1.5)


wake_word_service = WakeWordListener()
