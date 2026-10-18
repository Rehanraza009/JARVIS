"""
Unit tests for Task Manager, Document Reader, and Action Registry.
"""

import pytest
import tempfile
from pathlib import Path
from jarvis.tools.tasks_manager import TaskManager
from jarvis.tools.doc_reader import DocumentReader
from jarvis.tools.system_tools import SystemTools
from jarvis.tools.action_registry import ActionRegistry, PermissionLevel
from jarvis.memory.database import DatabaseManager


@pytest.fixture
def temp_task_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_tasks.db"
        manager = DatabaseManager(db_path=db_path)
        tm = TaskManager(manager=manager)
        yield tm


def test_task_crud(temp_task_manager):
    tm = temp_task_manager
    t_id = tm.add_task(title="Prepare for Google interview", due_date="Tomorrow", priority="high")
    assert t_id > 0

    pending = tm.list_tasks(status="pending")
    assert len(pending) == 1
    assert pending[0]["title"] == "Prepare for Google interview"

    # Complete task
    assert tm.complete_task(t_id) is True
    assert len(tm.list_tasks(status="pending")) == 0
    assert len(tm.list_tasks(status="completed")) == 1

    # Delete task
    assert tm.delete_task(t_id) is True
    assert len(tm.list_tasks()) == 0


def test_task_intent_detection(temp_task_manager):
    tm = temp_task_manager
    intent = tm.detect_task_intent("Remind me to submit project report by tomorrow")
    assert intent is not None
    assert intent["action"] == "add"
    assert "project report" in intent["title"]

    intent_list = tm.detect_task_intent("Show my pending tasks")
    assert intent_list is not None
    assert intent_list["action"] == "list"

    intent_comp = tm.detect_task_intent("Complete task #3")
    assert intent_comp is not None
    assert intent_comp["action"] == "complete"
    assert intent_comp["task_id"] == 3


def test_document_reader_text():
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as f:
        f.write("JARVIS document test content for Rehan Raza.")
        f_path = f.name

    try:
        res = DocumentReader.read_file(f_path)
        assert res["success"] is True
        assert "JARVIS document test content" in res["content"]

        # Test non-existent file
        res_missing = DocumentReader.read_file("non_existent_file_abc.txt")
        assert res_missing["success"] is False
    finally:
        Path(f_path).unlink(missing_ok=True)


def test_system_telemetry():
    data = SystemTools.get_system_telemetry()
    assert "time" in data
    assert "date" in data
    assert "os" in data


def test_action_registry_settings_commands():
    reg = ActionRegistry()
    # 1. "setting on karo"
    intent_setting_on = reg.detect_action_intent("setting on karo")
    assert intent_setting_on is not None
    assert intent_setting_on["action"] == "open_settings"
    assert intent_setting_on["kwargs"]["target"] == "main"

    # 2. "Windows settings open karo"
    intent_win_settings = reg.detect_action_intent("Windows settings open karo")
    assert intent_win_settings is not None
    assert intent_win_settings["action"] == "open_settings"

    # 3. "Bluetooth settings kholo"
    intent_bt = reg.detect_action_intent("Bluetooth settings kholo")
    assert intent_bt is not None
    assert intent_bt["action"] == "open_settings"
    assert intent_bt["kwargs"]["target"] == "bluetooth"

    # 4. "Jarvis settings kholo"
    intent_jarvis_settings = reg.detect_action_intent("Jarvis settings kholo")
    assert intent_jarvis_settings is not None
    assert intent_jarvis_settings["action"] == "navigate_ui"
    assert intent_jarvis_settings["kwargs"]["tab"] == "settings"


def test_action_registry_app_commands():
    reg = ActionRegistry()
    # Chrome
    intent_chrome = reg.detect_action_intent("Chrome kholo")
    assert intent_chrome is not None
    assert intent_chrome["action"] == "open_app"
    assert intent_chrome["kwargs"]["app_name"] == "chrome"

    # Paint
    intent_paint = reg.detect_action_intent("Paint kholo")
    assert intent_paint is not None
    assert intent_paint["action"] == "open_app"
    assert intent_paint["kwargs"]["app_name"] == "paint"

    # Unknown app
    intent_unknown = reg.detect_action_intent("Photoshop kholo")
    assert intent_unknown is not None
    assert intent_unknown["action"] == "open_app"
    # Execute unknown app -> should report honest failure/rejection
    res = reg.execute("open_app", app_name="unknown_app_xyz_123")
    assert res["success"] is False or res["result"]["success"] is False


def test_action_registry_window_and_power():
    reg = ActionRegistry()
    # Window minimize
    intent_min = reg.detect_action_intent("Window minimize karo")
    assert intent_min is not None
    assert intent_min["action"] == "minimize_window"

    # Window maximize
    intent_max = reg.detect_action_intent("Window maximize karo")
    assert intent_max is not None
    assert intent_max["action"] == "maximize_window"

    # Shutdown requires confirmation
    intent_shutdown = reg.detect_action_intent("Laptop shutdown karo")
    assert intent_shutdown is not None
    assert intent_shutdown["action"] == "shutdown_system"
    assert intent_shutdown["permission"] == PermissionLevel.CONFIRMATION_REQUIRED
