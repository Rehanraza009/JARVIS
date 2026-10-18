"""
Base abstract class for LLM providers in JARVIS.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Generator, Optional


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'gemini', 'openai', 'offline')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if required API keys/models/services are accessible."""
        pass

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> str:
        """Generate a complete text response."""
        pass

    def stream_response(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_instruction: str = ""
    ) -> Generator[str, None, None]:
        """Stream response chunks (defaults to yielding complete response if streaming not supported)."""
        full = self.generate_response(prompt, history, system_instruction)
        yield full
