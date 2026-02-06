"""
Training data generation pipeline for grokken.

Generates book-level summarization and follow-up Q&A training data
from cleaned historical texts.
"""

from grokken.generation.analyzer import BookAnalyzer
from grokken.generation.books import GenerationHandler, get_handler, has_handler
from grokken.generation.config import GenerationConfig, load_config, save_config
from grokken.generation.generator import Generator, PipelineResult
from grokken.generation.providers.base import (
    AuthenticationError,
    ContextLengthError,
    GenerationResult,
    LLMProvider,
    ProviderError,
    RateLimitError,
)
from grokken.generation.providers.openai import OpenAIProvider, create_provider
from grokken.generation.schema import BookSummaryRecord, QATurn, Segment
from grokken.generation.segmenter import Segmenter
from grokken.generation.simulated_user import SimulatedUser

__all__ = [
    # Core classes
    "BookAnalyzer",
    "BookSummaryRecord",
    "GenerationHandler",
    "get_handler",
    "has_handler",
    "GenerationConfig",
    "Generator",
    "GenerationResult",
    "PipelineResult",
    "QATurn",
    "Segment",
    "Segmenter",
    "SimulatedUser",
    # Config functions
    "load_config",
    "save_config",
    # Provider classes
    "LLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "create_provider",
    # Exceptions
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "ContextLengthError",
]


# Lazy import for AnthropicProvider (requires anthropic SDK)
def __getattr__(name: str) -> object:
    if name == "AnthropicProvider":
        from grokken.generation.providers.anthropic import AnthropicProvider

        return AnthropicProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
