"""
Configuration management for JARVIS.
Handles environment variables, default settings, and persistent user configuration.
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
AUDIO_DIR = DATA_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "jarvis_config.json"
MEMORY_DB_FILE = DATA_DIR / "jarvis_memory.db"
ENV_FILE = BASE_DIR / ".env"

# Load .env if present
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)


@dataclass
class UserProfileConfig:
    user_name: str = "Rehan Raza"
    preferred_address: str = "Rehan bhai"  # "Rehan bhai", "bhai", "Rehan"
    default_language: str = "Hinglish"     # "Hinglish", "Hindi", "English"
    tone_preference: str = "Warm, supportive, intelligent, natural friend"


@dataclass
class LLMConfig:
    provider: str = "gemini"               # "gemini", "openai", "offline"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1500


@dataclass
class SpeechConfig:
    stt_enabled: bool = True
    stt_language: str = "en-IN"            # "en-IN", "hi-IN", "en-US"
    tts_engine: str = "edge-tts"           # "edge-tts", "pyttsx3"
    edge_voice: str = "hi-IN-SwaraNeural"  # Default natural female voice
    female_hindi_voice: str = "hi-IN-SwaraNeural"
    female_english_voice: str = "en-IN-NeerjaNeural"
    speech_rate: str = "+0%"
    speech_volume: str = "+0%"
    pyttsx3_rate: int = 175
    pyttsx3_volume: float = 1.0
    listening_mode: str = "push_to_talk"   # "push_to_talk", "continuous", "wake_word"
    is_mic_muted: bool = False
    wake_word_enabled: bool = False
    wake_words: List[str] = field(default_factory=lambda: ["hey jarvis", "jarvis", "jarvis bhai"])
    listen_timeout_seconds: int = 6


@dataclass
class StartupConfig:
    launch_on_startup: bool = False
    play_startup_greeting: bool = True
    startup_greeting_muted: bool = False
    last_greeting_date: str = ""


@dataclass
class SystemToolsConfig:
    web_search_enabled: bool = True
    max_search_results: int = 4
    require_confirmation_for_scripts: bool = True
    privacy_mode: bool = False


@dataclass
class JarvisConfig:
    user: UserProfileConfig = field(default_factory=UserProfileConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    speech: SpeechConfig = field(default_factory=SpeechConfig)
    startup: StartupConfig = field(default_factory=StartupConfig)
    tools: SystemToolsConfig = field(default_factory=SystemToolsConfig)

    @classmethod
    def load(cls) -> "JarvisConfig":
        config = cls()
        
        # Load environment overrides
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "")

        if gemini_key:
            config.llm.gemini_api_key = gemini_key
        if openai_key:
            config.llm.openai_api_key = openai_key
        if openai_base:
            config.llm.openai_base_url = openai_base
        if default_provider in ["gemini", "openai", "offline"]:
            config.llm.provider = default_provider
        elif gemini_key:
            config.llm.provider = "gemini"
        elif openai_key:
            config.llm.provider = "openai"
        else:
            config.llm.provider = "offline"

        # Load persisted JSON config if exists
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "user" in data:
                    config.user = UserProfileConfig(**data["user"])
                if "llm" in data:
                    saved_llm = data["llm"]
                    # Retain env keys if not saved in json
                    if not saved_llm.get("gemini_api_key") and gemini_key:
                        saved_llm["gemini_api_key"] = gemini_key
                    if not saved_llm.get("openai_api_key") and openai_key:
                        saved_llm["openai_api_key"] = openai_key
                    config.llm = LLMConfig(**saved_llm)
                if "speech" in data:
                    config.speech = SpeechConfig(**data["speech"])
                if "startup" in data:
                    config.startup = StartupConfig(**data["startup"])
                if "tools" in data:
                    config.tools = SystemToolsConfig(**data["tools"])
            except Exception as e:
                print(f"[JarvisConfig] Warning: Failed to load {CONFIG_FILE}: {e}")

        return config

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[JarvisConfig] Warning: Failed to save {CONFIG_FILE}: {e}")


# Global config instance
active_config = JarvisConfig.load()
