"""
Tests for fast voice-to-action local routing, process management,
and security confirmations in JARVIS.
"""

import pytest
from unittest.mock import patch, MagicMock
from jarvis.tools.action_registry import action_registry, PermissionLevel
from jarvis.tools.system_tools import system_tools
from jarvis.conversation.conversation_manager import conversation_manager


def test_open_chrome_fast_intent():
    intent = action_registry.detect_action_intent("Chrome kholo")
    assert intent is not None
    assert intent["action"] == "open_app"
    assert intent["kwargs"]["app_name"] == "chrome"
    assert intent["permission"] == PermissionLevel.SAFE


def test_open_whatsapp_fast_intent():
    intent = action_registry.detect_action_intent("WhatsApp kholo")
    assert intent is not None
    assert intent["action"] == "open_app"
    assert intent["kwargs"]["app_name"] == "whatsapp"
    assert intent["permission"] == PermissionLevel.SAFE


def test_close_notepad_fast_intent():
    intent = action_registry.detect_action_intent("Notepad band karo")
    assert intent is not None
    assert intent["action"] == "close_app"
    assert intent["kwargs"]["app_name"] == "notepad"
    assert intent["permission"] == PermissionLevel.SAFE


def test_close_chrome_fast_intent():
    intent = action_registry.detect_action_intent("Chrome band karo")
    assert intent is not None
    assert intent["action"] == "close_app"
    assert intent["kwargs"]["app_name"] == "chrome"
    assert intent["permission"] == PermissionLevel.SAFE


def test_open_windows_settings_fast_intent():
    intent = action_registry.detect_action_intent("Windows Settings kholo")
    assert intent is not None
    assert intent["action"] == "open_settings"
    assert intent["kwargs"]["target"] == "main"
    assert intent["permission"] == PermissionLevel.SAFE


def test_volume_control_intents():
    intent_up = action_registry.detect_action_intent("volume badhao")
    assert intent_up is not None
    assert intent_up["action"] == "change_volume"
    assert intent_up["kwargs"]["direction"] == "up"

    intent_down = action_registry.detect_action_intent("volume kam karo")
    assert intent_down is not None
    assert intent_down["action"] == "change_volume"
    assert intent_down["kwargs"]["direction"] == "down"

    intent_mute = action_registry.detect_action_intent("sound mute karo")
    assert intent_mute is not None
    assert intent_mute["action"] == "change_volume"
    assert intent_mute["kwargs"]["direction"] == "mute"


def test_destructive_action_requires_confirmation():
    shutdown_intent = action_registry.detect_action_intent("laptop shutdown karo")
    assert shutdown_intent is not None
    assert shutdown_intent["action"] == "shutdown_system"
    assert shutdown_intent["permission"] == PermissionLevel.CONFIRMATION_REQUIRED

    restart_intent = action_registry.detect_action_intent("laptop restart karo")
    assert restart_intent is not None
    assert restart_intent["action"] == "restart_system"
    assert restart_intent["permission"] == PermissionLevel.CONFIRMATION_REQUIRED


def test_hinglish_variations_normalization():
    variations = [
        ("jarvis, chrome khol do", "open_app", "chrome"),
        ("google chrome open karo", "open_app", "chrome"),
        ("jarvis notepad close karo", "close_app", "notepad"),
        ("whatsapp band kar do", "close_app", "whatsapp"),
        ("bluetooth settings kholo", "open_settings", "bluetooth"),
        ("wifi settings open karo", "open_settings", "wifi")
    ]
    for phrase, expected_action, expected_arg in variations:
        res = action_registry.detect_action_intent(phrase)
        assert res is not None, f"Failed for phrase: '{phrase}'"
        assert res["action"] == expected_action
        if "app_name" in res["kwargs"]:
            assert res["kwargs"]["app_name"] == expected_arg
        elif "target" in res["kwargs"]:
            assert res["kwargs"]["target"] == expected_arg


@patch("subprocess.Popen")
def test_open_whatsapp_execution(mock_popen):
    res = system_tools.open_app("whatsapp")
    assert res["success"] is True
    assert "WhatsApp" in res["message"]
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert "whatsapp:" in args[0]


@patch("subprocess.run")
def test_close_app_execution(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "SUCCESS: The process \"notepad.exe\" has been terminated."
    mock_run.return_value = mock_res

    res = system_tools.close_app("notepad")
    assert res["success"] is True
    assert "Notepad band kar diya hai" in res["message"]
    mock_run.assert_called_once()
    assert "notepad.exe" in mock_run.call_args[0][0]


def test_conversation_manager_fast_bypass():
    with patch.object(action_registry, "execute") as mock_exec:
        mock_exec.return_value = {
            "success": True,
            "result": {"success": True, "message": "Chrome open kar diya hai Rehan bhai."}
        }
        response = conversation_manager.process_message("Chrome kholo")
        assert "Chrome" in response
        mock_exec.assert_called_once_with("open_app", app_name="chrome")


def test_open_folder_intents():
    intent_dl = action_registry.detect_action_intent("Downloads folder kholo")
    assert intent_dl is not None
    assert intent_dl["action"] == "open_folder"
    assert "download" in intent_dl["kwargs"]["folder_name"]

    intent_doc = action_registry.detect_action_intent("Documents folder kholo")
    assert intent_doc is not None
    assert intent_doc["action"] == "open_folder"
    assert "document" in intent_doc["kwargs"]["folder_name"]


def test_voice_listening_control_intents():
    intent_stop = action_registry.detect_action_intent("Jarvis, stop listening")
    assert intent_stop is not None
    assert intent_stop["action"] == "stop_listening"

    intent_resume = action_registry.detect_action_intent("Jarvis, listen again")
    assert intent_resume is not None
    assert intent_resume["action"] == "start_listening"


def test_app_on_and_close_variants():
    intent_chrome_on = action_registry.detect_action_intent("Chrome on karo")
    assert intent_chrome_on is not None
    assert intent_chrome_on["action"] == "open_app"
    assert intent_chrome_on["kwargs"]["app_name"] == "chrome"

    intent_chrome_close = action_registry.detect_action_intent("Chrome close karo")
    assert intent_chrome_close is not None
    assert intent_chrome_close["action"] == "close_app"
    assert intent_chrome_close["kwargs"]["app_name"] == "chrome"


def test_jarvis_settings_close_intent():
    intent_close_set = action_registry.detect_action_intent("JARVIS settings band karo")
    assert intent_close_set is not None
    assert intent_close_set["action"] == "navigate_ui"
    assert intent_close_set["kwargs"]["tab"] == "chat"


def test_daily_plan_and_completed_intents():
    from jarvis.tools.tasks_manager import task_manager
    intent_plan = task_manager.detect_task_intent("Aaj ka plan batao")
    assert intent_plan is not None
    assert intent_plan["action"] == "daily_plan"

    intent_done = task_manager.detect_task_intent("Maine aaj kya-kya complete kiya?")
    assert intent_done is not None
    assert intent_done["action"] == "completed_today"


def test_goals_memory_intent():
    from jarvis.memory.memory_service import memory_service
    intent_goals = memory_service.detect_natural_memory_intent("Mere current goals kya hain?")
    assert intent_goals is not None
    assert intent_goals["action"] == "goals"


@patch("os.startfile")
def test_open_folder_execution(mock_startfile):
    res = system_tools.open_folder("downloads")
    assert res["success"] is True
    assert "folder khol diya" in res["message"]
    mock_startfile.assert_called_once()
