"""
Google Gemini LLM provider for JARVIS.
"""

from typing import List, Dict, Generator, Optional
from jarvis.llm.base import BaseLLMProvider
from jarvis.core.logger import jarvis_logger
import os
import warnings

# Suppress deprecation warning from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
warnings.filterwarnings("ignore", message=".*google.generativeai.*")

try:
    import google.generativeai as genai
    HAS_GEMINI_LIB = True
except ImportError:
    HAS_GEMINI_LIB = False


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or "gemini-1.5-flash"
        self._configured = False
        self._init_client()

    def _init_client(self):
        if HAS_GEMINI_LIB and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._configured = True
                jarvis_logger.info(f"Gemini client initialized with model '{self.model_name}'")
            except Exception as e:
                jarvis_logger.warning(f"Failed to configure Gemini client: {e}")
                self._configured = False

    @property
    def provider_name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return HAS_GEMINI_LIB and bool(self.api_key) and self._configured

    def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini provider is not configured or missing an API key.")

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction if system_instruction else None
            )

            # Format conversation history
            contents = []
            if history:
                for msg in history:
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append({"role": role, "parts": [msg.get("content", "")]})

            contents.append({"role": "user", "parts": [prompt]})

            response = model.generate_content(contents)
            if response and response.text:
                return response.text.strip()
            return "Mujhe samajh nahi aaya, Rehan bhai. Kya aap dubara bata sakte hain?"
        except Exception as e:
            jarvis_logger.error(f"Gemini generation error: {e}")
            raise e

    def stream_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> Generator[str, None, None]:
        if not self.is_available():
            raise RuntimeError("Gemini provider is not configured or missing an API key.")

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction if system_instruction else None
            )

            contents = []
            if history:
                for msg in history:
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append({"role": role, "parts": [msg.get("content", "")]})

            contents.append({"role": "user", "parts": [prompt]})

            response = model.generate_content(contents, stream=True)
            for chunk in response:
                if chunk and chunk.text:
                    yield chunk.text
        except Exception as e:
            jarvis_logger.error(f"Gemini streaming error: {e}")
            raise e
