"""
Provider factory for dynamically instantiating LLM backends with automatic fallback.
"""

from typing import Optional
from jarvis.core.config import active_config
from jarvis.core.logger import jarvis_logger
from jarvis.llm.base import BaseLLMProvider
from jarvis.llm.gemini_provider import GeminiProvider
from jarvis.llm.openai_provider import OpenAIProvider
from jarvis.llm.offline_provider import OfflineProvider


class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
        target = (provider_type or active_config.llm.provider or "gemini").lower().strip()
        
        jarvis_logger.info(f"Resolving LLM provider for type: '{target}'")

        if target == "gemini":
            provider = GeminiProvider(
                api_key=active_config.llm.gemini_api_key,
                model_name=active_config.llm.gemini_model
            )
            if provider.is_available():
                return provider
            jarvis_logger.warning("Gemini is not available (missing key or library). Attempting fallback.")

        if target == "openai" or (target != "offline" and active_config.llm.openai_api_key):
            provider = OpenAIProvider(
                api_key=active_config.llm.openai_api_key,
                base_url=active_config.llm.openai_base_url,
                model_name=active_config.llm.openai_model
            )
            if provider.is_available():
                return provider
            jarvis_logger.warning("OpenAI provider is not available. Falling back to offline provider.")

        # Default guaranteed fallback
        return OfflineProvider()


def get_active_llm() -> BaseLLMProvider:
    return LLMProviderFactory.get_provider()
