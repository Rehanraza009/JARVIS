"""
Audio player with instant interruption support for JARVIS.
Uses PySide6 QtMultimedia QMediaPlayer or Windows native APIs.
"""

import os
import threading
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QUrl, QObject, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from jarvis.core.logger import jarvis_logger
from jarvis.core.events import bus, AssistantState


class InterruptibleAudioPlayer(QObject):
    playback_finished = Signal()

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        self.is_playing = False
        self._lock = threading.Lock()

        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_player_error)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            with self._lock:
                was_playing = self.is_playing
                self.is_playing = False
            if was_playing:
                bus.speech_finished.emit()
                bus.state_changed.emit(AssistantState.IDLE)
                self.playback_finished.emit()

    def _on_player_error(self, error, error_string=""):
        jarvis_logger.warning(f"Audio player error: {error} - {error_string}")
        with self._lock:
            self.is_playing = False
        bus.speech_finished.emit()
        bus.state_changed.emit(AssistantState.IDLE)
        self.playback_finished.emit()

    def play_file(self, file_path: str):
        """Play an audio file (MP3/WAV) with interruptibility."""
        path = Path(file_path).resolve()
        if not path.exists():
            jarvis_logger.warning(f"Audio file '{path}' does not exist.")
            return

        self.stop()

        with self._lock:
            self.is_playing = True

        bus.state_changed.emit(AssistantState.SPEAKING)
        url = QUrl.fromLocalFile(str(path))
        self.player.setSource(url)
        self.player.play()
        jarvis_logger.info(f"Started audio playback: {path.name}")

    def stop(self):
        """Immediately interrupt and stop playback."""
        with self._lock:
            if self.is_playing or self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.stop()
                self.is_playing = False
                bus.speech_finished.emit()
                bus.state_changed.emit(AssistantState.IDLE)
                jarvis_logger.info("Audio playback interrupted/stopped.")


audio_player = InterruptibleAudioPlayer()
