"""
Unit tests for Personal Memory & Persistence System.
"""

import pytest
import tempfile
from pathlib import Path
from jarvis.memory.database import DatabaseManager
from jarvis.memory.memory_service import MemoryService


@pytest.fixture
def temp_memory_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        manager = DatabaseManager(db_path=db_path)
        service = MemoryService(manager=manager)
        yield service


def test_save_and_retrieve_memory(temp_memory_service):
    service = temp_memory_service
    mem_id = service.save_memory(
        category="career",
        key="target_role",
        content="Wants to become a Senior AI & ML Engineer"
    )
    assert mem_id > 0

    retrieved = service.get_memory(mem_id)
    assert retrieved is not None
    assert retrieved["key"] == "target_role"
    assert "Senior AI" in retrieved["content"]


def test_update_memory(temp_memory_service):
    service = temp_memory_service
    mem_id = service.save_memory(
        category="project",
        key="jarvis_status",
        content="Building desktop assistant"
    )
    # Update same key in same category
    mem_id_2 = service.save_memory(
        category="project",
        key="jarvis_status",
        content="JARVIS desktop assistant completed with PySide6"
    )
    assert mem_id == mem_id_2

    updated = service.get_memory(mem_id)
    assert "completed" in updated["content"]


def test_search_memories(temp_memory_service):
    service = temp_memory_service
    service.save_memory("preference", "food", "Rehan likes Hyderabadi Biryani")
    service.save_memory("goal", "fitness", "Daily workout at 7am")

    results = service.search_memories("Biryani")
    assert len(results) == 1
    assert results[0]["key"] == "food"

    results_none = service.search_memories("nonexistenttopic12345")
    assert len(results_none) == 0


def test_delete_and_wipe(temp_memory_service):
    service = temp_memory_service
    m1 = service.save_memory("fact", "os", "Windows 11")
    m2 = service.save_memory("fact", "editor", "VS Code")

    assert len(service.list_memories()) == 2
    assert service.delete_memory(m1) is True
    assert len(service.list_memories()) == 1

    count = service.delete_all_memories()
    assert count == 1
    assert len(service.list_memories()) == 0


def test_natural_memory_intent(temp_memory_service):
    service = temp_memory_service

    # Remember intent
    intent = service.detect_natural_memory_intent("Jarvis remember that I have an interview tomorrow")
    assert intent is not None
    assert intent["action"] == "remember"
    assert "interview" in intent["content"]

    # Recall intent
    intent_recall = service.detect_natural_memory_intent("What do you remember about me?")
    assert intent_recall is not None
    assert intent_recall["action"] == "recall"

    # Forget intent
    intent_forget = service.detect_natural_memory_intent("Jarvis forget that interview")
    assert intent_forget is not None
    assert intent_forget["action"] == "forget"
    assert "interview" in intent_forget["query"]

    # Delete all intent
    intent_wipe = service.detect_natural_memory_intent("Delete all memories")
    assert intent_wipe is not None
    assert intent_wipe["action"] == "delete_all"


def test_export_import_json(temp_memory_service):
    service = temp_memory_service
    service.save_memory("preference", "theme", "Dark navy theme")
    json_str = service.export_memories_json()
    assert "Dark navy theme" in json_str

    service.delete_all_memories()
    assert len(service.list_memories()) == 0

    count = service.import_memories_json(json_str)
    assert count == 1
    assert len(service.list_memories()) == 1
