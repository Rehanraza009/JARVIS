"""
Unit and integration tests for Companion Widget, Hands-Free Voice loop,
Wake-Word detection, and AI question-answering.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication

from jarvis.core.events import bus, AssistantState
from jarvis.speech.wake_word import WakeWordListener
from jarvis.speech.stt_engine import STTEngine
from jarvis.llm.offline_provider import OfflineProvider
from jarvis.conversation.conversation_manager import conversation_manager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_companion_widget_signals_and_state(qapp):
    from jarvis.ui.companion_widget import CompanionWidget
    companion = CompanionWidget()
    assert companion.isWindow()
    assert companion.width() == 390
    assert companion.height() == 240

    # Test state change signal updates pill
    bus.state_changed.emit(AssistantState.LISTENING)
    assert "LISTENING" in companion.state_pill.text()

    bus.state_changed.emit(AssistantState.EXECUTING)
    assert "EXECUTING" in companion.state_pill.text()

    bus.state_changed.emit(AssistantState.SPEAKING)
    assert "SPEAKING" in companion.state_pill.text()

    # Test transcript update
    bus.transcript_updated.emit("Chrome kholo")
    assert "Chrome kholo" in companion.transcript_label.text()

    # Test action start / finished
    bus.action_started.emit("open_app", "{'app_name': 'chrome'}")
    assert "open_app" in companion.action_label.text()

    bus.action_finished.emit("open_app", True, "Chrome opened")
    assert "open_app" in companion.action_label.text()

    # Test answer display
    bus.message_received.emit("jarvis", "Chrome open kar diya hai Rehan bhai.")
    assert "Chrome open" in companion.answer_label.text()

    companion.close()


def test_wake_word_combined_command_parsing():
    wake_listener = WakeWordListener()
    callback_mock = MagicMock()
    wake_listener.on_wake_callback = callback_mock

    # Test combined phrase: "Hey Jarvis Chrome kholo"
    phrase = "hey jarvis chrome kholo"
    wake_phrases = ["hey jarvis", "jarvis"]
    matched_wake = "hey jarvis"
    import re
    remainder = re.sub(rf"^.*?{re.escape(matched_wake)}\s*,?\s*", "", phrase).strip()
    assert remainder == "chrome kholo"

    # Test wake word only: "Hey Jarvis"
    phrase_only = "hey jarvis"
    remainder_only = re.sub(rf"^.*?{re.escape(matched_wake)}\s*,?\s*", "", phrase_only).strip()
    assert remainder_only == ""


def test_stt_engine_turn_processing_and_echo_guard():
    stt = STTEngine()
    assert stt._is_processing_turn is False
    assert stt._turn_finished_event.is_set()

    # Assistant starts speaking -> turn locked
    bus.speech_started.emit("Hello Rehan bhai")
    assert stt._is_assistant_speaking is True
    assert stt._is_processing_turn is True
    assert not stt._turn_finished_event.is_set()

    # Assistant speech finished -> speech cleared after delay
    bus.speech_finished.emit()
    import time
    time.sleep(0.9)
    assert stt._is_assistant_speaking is False
    assert stt._is_processing_turn is False
    assert stt._turn_finished_event.is_set()


def test_ai_question_answering_ml_and_ai():
    provider = OfflineProvider()

    # 1. Explain Machine Learning
    ml_resp = provider.generate_response("Explain machine learning")
    assert "Machine Learning" in ml_resp
    assert "Supervised Learning" in ml_resp

    # Follow up to ML
    history = [
        {"role": "user", "content": "Explain machine learning"},
        {"role": "assistant", "content": ml_resp}
    ]
    followup_resp = provider.generate_response("What is the difference with deep learning?", history=history)
    assert "Deep Learning" in followup_resp
    assert "neural network" in followup_resp.lower()

    # 2. What is happening in AI?
    ai_resp = provider.generate_response("What is happening in AI?")
    assert "AI" in ai_resp
    assert "Autonomous" in ai_resp or "Agent" in ai_resp or "Reasoning" in ai_resp

    # 3. Help me solve this problem
    prob_resp = provider.generate_response("Help me solve this problem")
    assert "solve" in prob_resp.lower() or "diagnose" in prob_resp.lower() or "error" in prob_resp.lower()


def test_single_instance_ipc_socket(qapp):
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    test_socket_name = "TEST_JARVIS_SINGLE_INSTANCE_IPC"

    server = QLocalServer()
    server.removeServer(test_socket_name)
    assert server.listen(test_socket_name) is True

    # Client connects
    client = QLocalSocket()
    client.connectToServer(test_socket_name)
    assert client.waitForConnected(500) is True

    client.write(b"SHOW\n")
    client.waitForBytesWritten(500)
    client.disconnectFromServer()

    server.close()
    server.removeServer(test_socket_name)
