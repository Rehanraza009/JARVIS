"""
Unit tests for Speech and Voice System (TTS and STT).
"""

import pytest
from jarvis.speech.tts_engine import TTSEngine
from jarvis.speech.stt_engine import STTEngine
from jarvis.speech.audio_player import InterruptibleAudioPlayer
from jarvis.core.events import bus, AssistantState


def test_tts_clean_text():
    raw_markdown = """
    Hello **Rehan bhai**! Check out [Google](https://google.com) for details.
    ```python
    def secret():
        pass
    ```
    • First point
    • Second point
    """
    cleaned = TTSEngine.clean_text_for_speech(raw_markdown)
    assert "**" not in cleaned
    assert "https://google.com" not in cleaned
    assert "Google" in cleaned
    assert "secret():" not in cleaned
    assert "Rehan bhai" in cleaned


def test_female_voice_resolution():
    engine = TTSEngine()
    # Hindi/Hinglish text should resolve to female hindi voice (Swara)
    voice_hi = engine.resolve_voice_for_text("Arey Rehan bhai, kya haal chal?")
    assert "Swara" in voice_hi

    # English text should resolve to female english voice (Neerja)
    voice_en = engine.resolve_voice_for_text("What is a dictionary in Python programming language?")
    assert "Neerja" in voice_en or "Jenny" in voice_en


def test_stt_engine_language_and_mute():
    engine = STTEngine()
    assert engine.language in ["en-IN", "hi-IN", "en-US"]

    # Test Mute
    engine.set_muted(True)
    assert engine.is_muted is True
    engine.set_muted(False)
    assert engine.is_muted is False


def test_audio_player_stop():
    player = InterruptibleAudioPlayer()
    player.stop()
    assert player.is_playing is False
