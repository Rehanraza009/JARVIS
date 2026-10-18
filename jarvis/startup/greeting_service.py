"""
Startup Greeting service for JARVIS.
Generates dynamic, time-aware, warm greetings for Rehan Raza.
Prevents duplicate greetings within the same login session.
"""

import random
import json
from datetime import datetime
from typing import Optional
from jarvis.core.config import active_config, DATA_DIR
from jarvis.core.logger import jarvis_logger
from jarvis.speech.tts_engine import tts_engine
from jarvis.core.events import bus

SESSION_TRACKER_FILE = DATA_DIR / "startup_session.json"


class GreetingService:
    MORNING_GREETINGS = [
        "Good morning, Rehan bhai! Kaise ho? Aaj kya plan hai?",
        "Good morning Rehan bhai! Uth gaye? Aaj kis project par kaam karein?",
        "Subah bakhair bhai! Main ready hoon, bataiye aaj kya plan hai."
    ]

    AFTERNOON_GREETINGS = [
        "Hello Rehan bhai! Welcome back. Aaj kis cheez mein help karun?",
        "Good afternoon Rehan bhai! Kaam kaisa chal raha hai? Bataiye kisi cheez mein help chahiye?",
        "Hello bhai! Welcome back. Main ready hoon, bataiye kya discuss karein?"
    ]

    EVENING_GREETINGS = [
        "Hey Rehan bhai! Kaisa raha aaj ka din?",
        "Good evening Rehan bhai! Thakaan ho gayi kya? Bataiye kaisa beeta aaj ka din.",
        "Welcome back, bhai! Aaj ka din kaisa raha? Aaram se baithte hain aur baat karte hain."
    ]

    NIGHT_GREETINGS = [
        "Late night work chal raha hai Rehan bhai? Thoda rest bhi le lena, baki main hoon yahan.",
        "Hello Rehan bhai! Raat ka shaant waqt hai, bataiye kis project par deep work karna hai?",
        "Bhai raat kaafi ho gayi hai, par jab tak aap active ho main bhi saath hoon. Kahiye kya chal raha hai?"
    ]

    @classmethod
    def get_greeting_text(cls) -> str:
        """Generate time-aware greeting for Rehan bhai."""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return random.choice(cls.MORNING_GREETINGS)
        elif 12 <= hour < 17:
            return random.choice(cls.AFTERNOON_GREETINGS)
        elif 17 <= hour < 22:
            return random.choice(cls.EVENING_GREETINGS)
        else:
            return random.choice(cls.NIGHT_GREETINGS)

    @classmethod
    def should_play_greeting(cls) -> bool:
        """Check if startup greeting is enabled, not muted, and hasn't played today/session."""
        if not active_config.startup.play_startup_greeting:
            return False
        if active_config.startup.startup_greeting_muted:
            return False

        today_str = datetime.now().strftime("%Y-%m-%d")

        if SESSION_TRACKER_FILE.exists():
            try:
                with open(SESSION_TRACKER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("last_greeting_date") == today_str:
                        jarvis_logger.info("Startup greeting already delivered today. Skipping repeat.")
                        return False
            except Exception as e:
                jarvis_logger.warning(f"Error reading session file: {e}")

        return True

    @classmethod
    def record_greeting_played(cls):
        """Mark greeting as played for today."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            with open(SESSION_TRACKER_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_greeting_date": today_str, "timestamp": datetime.now().isoformat()}, f)
        except Exception as e:
            jarvis_logger.warning(f"Error recording greeting session: {e}")

    @classmethod
    def deliver_startup_greeting(cls, force: bool = False):
        """Deliver the spoken and textual startup greeting."""
        if not force and not cls.should_play_greeting():
            return

        greeting = cls.get_greeting_text()
        jarvis_logger.info(f"Delivering startup greeting: '{greeting}'")

        # Emit to UI
        bus.message_received.emit("jarvis", greeting)

        # Spoken greeting
        if not active_config.startup.startup_greeting_muted:
            tts_engine.speak(greeting)

        if not force:
            cls.record_greeting_played()


greeting_service = GreetingService()
