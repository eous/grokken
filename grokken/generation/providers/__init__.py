"""
LLM providers for text generation.
"""

from grokken.generation.providers.base import LLMProvider
from grokken.generation.providers.openai import OpenAIProvider

__all__ = ["LLMProvider", "OpenAIProvider", "AnthropicProvider"]


# Lazy import for AnthropicProvider (requires anthropic SDK)
def __getattr__(name: str) -> object:
    if name == "AnthropicProvider":
        from grokken.generation.providers.anthropic import AnthropicProvider

        return AnthropicProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
