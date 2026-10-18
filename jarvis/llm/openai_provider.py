"""
OpenAI & Compatible (Groq, DeepSeek, Local Ollama) LLM provider for JARVIS.
"""

from typing import List, Dict, Generator, Optional
import os
from jarvis.llm.base import BaseLLMProvider
from jarvis.core.logger import jarvis_logger

try:
    from openai import OpenAI
    HAS_OPENAI_LIB = True
except ImportError:
    HAS_OPENAI_LIB = False


class OpenAIProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o-mini"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or "gpt-4o-mini"
        self.client = None
        self._init_client()

    def _init_client(self):
        if HAS_OPENAI_LIB and (self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url):
            try:
                # Ollama or local endpoint might not require an actual key, can use dummy 'ollama'
                key = self.api_key if self.api_key else "ollama-local"
                self.client = OpenAI(api_key=key, base_url=self.base_url)
                jarvis_logger.info(f"OpenAI client initialized for model '{self.model_name}' at {self.base_url}")
            except Exception as e:
                jarvis_logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        return HAS_OPENAI_LIB and self.client is not None

    def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> str:
        if not self.is_available():
            raise RuntimeError("OpenAI provider is not configured or missing an API key.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        if history:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            jarvis_logger.error(f"OpenAI completion error: {e}")
            raise e

    def stream_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> Generator[str, None, None]:
        if not self.is_available():
            raise RuntimeError("OpenAI provider is not configured or missing an API key.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        if history:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                temperature=0.7
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            jarvis_logger.error(f"OpenAI stream error: {e}")
            raise e
