"""
Event dispatching bus for JARVIS.
Allows decoupled communication between background threads, LLM, speech, memory, and UI.
"""

from enum import Enum
from typing import Callable, Dict, List, Any
from PySide6.QtCore import QObject, Signal


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    ERROR = "error"


class EventSignals(QObject):
    """Qt Signal bridge for thread-safe UI updates."""
    state_changed = Signal(str)                   # AssistantState value
    message_received = Signal(str, str)          # sender ("user" or "jarvis"), text
    speech_detected = Signal(str)                # transcribed speech text
    speech_started = Signal(str)                 # text being spoken
    speech_finished = Signal()                   # spoken audio ended
    status_updated = Signal(str, str)            # component_name, status_message
    memory_changed = Signal()                    # triggered when memories are added/removed
    tasks_changed = Signal()                     # triggered when tasks are updated
    error_occurred = Signal(str, str)            # title, details
    navigation_requested = Signal(str)           # tab name ("settings", "chat", "memory", "tasks", "tools")
    listening_mode_changed = Signal(str)         # "push_to_talk", "continuous", "wake_word"
    mic_mute_toggled = Signal(bool)              # True if muted
    action_confirmation_requested = Signal(str, str) # title, prompt text
    action_started = Signal(str, str)            # action_name, description
    action_finished = Signal(str, bool, str)     # action_name, success, message
    transcript_updated = Signal(str)             # live partial/completed transcript
    companion_toggled = Signal(bool)             # True to show, False to hide


# Global signal bus instance for Qt
bus = EventSignals()
