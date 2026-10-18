"""
Unit tests for Jarvis configuration manager.
"""

import pytest
from jarvis.core.config import JarvisConfig, UserProfileConfig, LLMConfig


def test_default_config():
    config = JarvisConfig()
    assert config.user.user_name == "Rehan Raza"
    assert config.user.preferred_address == "Rehan bhai"
    assert config.user.default_language == "Hinglish"
    assert config.llm.temperature == 0.7


def test_custom_user_config():
    config = JarvisConfig(user=UserProfileConfig(user_name="Rehan", preferred_address="bhai"))
    assert config.user.user_name == "Rehan"
    assert config.user.preferred_address == "bhai"
