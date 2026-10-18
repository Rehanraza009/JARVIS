"""
Unit tests for Windows Startup & Greeting Service.
"""

import pytest
from jarvis.startup.greeting_service import GreetingService
from jarvis.startup.windows_startup import WindowsStartupManager


def test_greeting_text_generation():
    greeting = GreetingService.get_greeting_text()
    assert isinstance(greeting, str)
    assert len(greeting) > 10
    # Must naturally address Rehan bhai or bhai
    assert "Rehan bhai" in greeting or "bhai" in greeting


def test_windows_startup_methods():
    # Verify method callable without unhandled crash
    is_enabled = WindowsStartupManager.is_startup_enabled()
    assert isinstance(is_enabled, bool)
