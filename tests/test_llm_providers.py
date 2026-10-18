"""
Unit tests for LLM Provider abstraction and Fallback Factory.
"""

import pytest
from jarvis.llm.offline_provider import OfflineProvider
from jarvis.llm.provider_factory import LLMProviderFactory


def test_offline_provider_responses():
    provider = OfflineProvider()
    assert provider.is_available() is True
    assert provider.provider_name == "offline"

    # Test presence query (female persona)
    resp = provider.generate_response("Jarvis, sun rahi ho?")
    assert "sun rahi hoon" in resp.lower()

    # Test mood check (female empathy)
    resp_mood = provider.generate_response("Jarvis bhai, aaj mood off hai.")
    assert "sun rahi hoon" in resp_mood.lower() or "heavy" in resp_mood.lower()

    # Test English query (language matching)
    resp_en = provider.generate_response("What is a dictionary in Python?")
    assert "key-value" in resp_en.lower() or "dictionary" in resp_en.lower()
    assert "sun rahi hoon" not in resp_en

    # Test follow-up handling with history
    history = [
        {"role": "user", "content": "Mere project mein login issue hai."},
        {"role": "assistant", "content": "Achha bhai, login par exactly kya ho raha hai?"}
    ]
    resp_login = provider.generate_response("Passenger login nahi ho raha", history=history)
    assert "passenger" in resp_login.lower()
    assert "debug" in resp_login.lower() or "backend" in resp_login.lower()


def test_offline_streaming():
    provider = OfflineProvider()
    chunks = list(provider.stream_response("Hello Jarvis"))
    assert len(chunks) > 0
    full = "".join(chunks)
    assert len(full) > 5


def test_provider_factory_fallback():
    # When requesting an unconfigured provider, factory safely falls back to offline
    provider = LLMProviderFactory.get_provider("offline")
    assert provider.is_available() is True
    assert provider.provider_name == "offline"
