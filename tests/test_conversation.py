"""
Unit tests for Conversation Context, Language Matching, and Orchestration.
"""

import pytest
import tempfile
from pathlib import Path
from jarvis.conversation.context_manager import ContextManager
from jarvis.conversation.prompt_templates import build_system_instruction
from jarvis.conversation.conversation_manager import ConversationManager
from jarvis.memory.database import DatabaseManager


@pytest.fixture
def temp_context_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_conv.db"
        manager = DatabaseManager(db_path=db_path)
        ctx = ContextManager(max_turns=3, manager=manager)
        yield ctx


def test_context_manager_rolling(temp_context_manager):
    ctx = temp_context_manager
    ctx.add_turn("user", "Hello 1")
    ctx.add_turn("assistant", "Hi 1")
    ctx.add_turn("user", "Hello 2")
    ctx.add_turn("assistant", "Hi 2")
    ctx.add_turn("user", "Hello 3")
    ctx.add_turn("assistant", "Hi 3")
    ctx.add_turn("user", "Hello 4")
    ctx.add_turn("assistant", "Hi 4")

    # max_turns=3, each turn has user+assistant = 6 messages max
    history = ctx.get_history_for_llm()
    assert len(history) <= 6
    assert history[-1]["content"] == "Hi 4"


def test_system_prompt_builder():
    memories = [
        {"category": "goal", "key": "career_aim", "content": "Become an AI researcher"}
    ]
    prompt = build_system_instruction(relevant_memories=memories, tool_context="Research info")
    assert "Rehan Raza" in prompt
    assert "Rehan bhai" in prompt
    assert "Become an AI researcher" in prompt
    assert "Research info" in prompt


def test_hindi_hinglish_response():
    mgr = ConversationManager()
    # Test mood check with female verb
    resp_mood = mgr.process_message("Jarvis bhai, aaj mood off hai.")
    assert any(w in resp_mood.lower() for w in ["sun rahi hoon", "heavy", "kya hua", "rehan"])

    # Test presence
    resp_presence = mgr.process_message("Jarvis, sun rahi ho?")
    assert any(w in resp_presence.lower() for w in ["sun rahi hoon", "active", "bhai"])


def test_english_response_matching():
    mgr = ConversationManager()
    resp_en = mgr.process_message("What is a dictionary in Python?")
    assert "key-value" in resp_en.lower() or "dictionary" in resp_en.lower()
    # Should not contain Hindi verbs
    assert "sun rahi hoon" not in resp_en


def test_followup_context_retention():
    mgr = ConversationManager()
    # Step 1
    mgr.process_message("Mere project mein login issue hai.")
    # Step 2: Follow-up without repeating "project"
    resp_step2 = mgr.process_message("Passenger login nahi ho raha")
    assert "passenger" in resp_step2.lower()
    assert any(w in resp_step2.lower() for w in ["backend", "debug", "status code", "validation"])


def test_action_execution_settings():
    mgr = ConversationManager()
    resp = mgr.process_message("setting on karo")
    assert any(w in resp.lower() for w in ["settings", "windows settings", "khol"])

    resp_jarvis = mgr.process_message("Jarvis settings kholo")
    assert "settings" in resp_jarvis.lower()
