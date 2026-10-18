"""
Text-to-Speech (TTS) engine for JARVIS.
Features natural Microsoft Edge neural female voices (Hindi, Hinglish, English)
with automatic language matching, offline pyttsx3 fallback, markdown cleanup,
and foolproof state recovery.
"""

import re
import uuid
import asyncio
import threading
from pathlib import Path
from typing import Optional, Callable
from jarvis.core.config import active_config, CACHE_DIR
from jarvis.core.logger import jarvis_logger
from jarvis.core.events import bus, AssistantState
from jarvis.speech.audio_player import audio_player

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


class TTSEngine:
    def __init__(self):
        self.edge_voice = active_config.speech.edge_voice or "hi-IN-SwaraNeural"
        self.female_hindi_voice = active_config.speech.female_hindi_voice or "hi-IN-SwaraNeural"
        self.female_english_voice = active_config.speech.female_english_voice or "en-IN-NeerjaNeural"
        self.pyttsx3_engine = None
        self._init_pyttsx3()

    def _init_pyttsx3(self):
        if HAS_PYTTSX3:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self.pyttsx3_engine.setProperty('rate', active_config.speech.pyttsx3_rate)
                self.pyttsx3_engine.setProperty('volume', active_config.speech.pyttsx3_volume)

                # Select a female voice on SAPI5 if available
                voices = self.pyttsx3_engine.getProperty('voices')
                for v in voices:
                    name_lower = v.name.lower()
                    if "zira" in name_lower or "female" in name_lower or "heera" in name_lower:
                        self.pyttsx3_engine.setProperty('voice', v.id)
                        jarvis_logger.info(f"pyttsx3 selected female voice: {v.name}")
                        break
            except Exception as e:
                jarvis_logger.warning(f"Failed to initialize pyttsx3: {e}")
                self.pyttsx3_engine = None

    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Strip markdown links, code blocks, bullets, and symbols for clean, natural speech."""
        # Remove code blocks
        clean = re.sub(r"```[\s\S]*?```", " Code snippet skipped. ", text)
        # Remove inline code
        clean = re.sub(r"`.*?`", "", clean)
        # Remove markdown URLs: [title](url) -> title
        clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
        # Remove bold/italic markers
        clean = re.sub(r"[*_#>`]", "", clean)
        # Remove bullets
        clean = re.sub(r"^\s*[-•*]\s+", "", clean, flags=re.MULTILINE)
        # Condense whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def resolve_voice_for_text(self, text: str, user_voice: Optional[str] = None) -> str:
        """Dynamically pick the best natural female voice matching the language."""
        if user_voice:
            return user_voice

        # Check for Devanagari or Hindi/Hinglish marker words
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in text)
        text_lower = text.lower()
        hinglish_words = [
            "kya", "hua", "hai", "karo", "kholo", "bhai", "rehan", "aaj", "kaise",
            "karna", "hoon", "saktee", "sakti", "rahi", "samajh", "batao", "baat", "mein"
        ]
        is_hinglish = any(re.search(r"\b" + w + r"\b", text_lower) for w in hinglish_words)

        if has_devanagari or is_hinglish:
            return self.female_hindi_voice
        else:
            return self.female_english_voice

    def speak(self, text: str, voice: Optional[str] = None):
        """Speak text asynchronously in a background thread."""
        clean = self.clean_text_for_speech(text)
        if not clean:
            bus.state_changed.emit(AssistantState.IDLE)
            return

        target_voice = self.resolve_voice_for_text(clean, user_voice=voice)

        # Notify speech pipeline immediately so listening doesn't re-trigger during Edge TTS download
        bus.speech_started.emit("synthesizing")
        bus.state_changed.emit(AssistantState.SPEAKING)

        # Launch thread to synthesize and play
        threading.Thread(
            target=self._synthesize_and_play,
            args=(clean, target_voice),
            daemon=True
        ).start()

    def _synthesize_and_play(self, text: str, voice: str):
        try:
            # 1. Try Edge TTS
            if HAS_EDGE_TTS:
                try:
                    audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
                    output_path = CACHE_DIR / audio_filename

                    async def _generate():
                        communicate = edge_tts.Communicate(
                            text,
                            voice,
                            rate=active_config.speech.speech_rate,
                            volume=active_config.speech.speech_volume
                        )
                        await communicate.save(str(output_path))

                    asyncio.run(_generate())

                    if output_path.exists() and output_path.stat().st_size > 0:
                        audio_player.play_file(str(output_path))
                        return
                except Exception as e:
                    jarvis_logger.warning(f"Edge TTS synthesis error: {e}. Falling back to pyttsx3.")

            # 2. Offline Fallback: pyttsx3
            if self.pyttsx3_engine:
                try:
                    bus.state_changed.emit(AssistantState.SPEAKING)
                    self.pyttsx3_engine.say(text)
                    self.pyttsx3_engine.runAndWait()
                    bus.speech_finished.emit()
                    bus.state_changed.emit(AssistantState.IDLE)
                    return
                except Exception as e:
                    jarvis_logger.error(f"pyttsx3 speech error: {e}")

            # If all speech options failed or no audio engine produced playback:
            bus.speech_finished.emit()
            bus.state_changed.emit(AssistantState.IDLE)

        except Exception as e:
            jarvis_logger.error(f"Speech synthesis critical error: {e}")
            bus.speech_finished.emit()
            bus.state_changed.emit(AssistantState.IDLE)

    def stop(self):
        """Interrupt and stop current speech."""
        audio_player.stop()
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.stop()
            except Exception:
                pass
        bus.state_changed.emit(AssistantState.IDLE)


tts_engine = TTSEngine()
