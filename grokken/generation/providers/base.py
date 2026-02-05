"""
Abstract base class for LLM providers.

Defines the interface that all providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenerationResult:
    """Result from an LLM generation call."""

    text: str
    input_tokens: int
    output_tokens: int
    model: str
    finish_reason: str | None = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implementations should handle:
    - API authentication
    - Rate limiting and retries
    - Token counting
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier being used."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: float | None = None,
    ) -> GenerationResult:
        """
        Generate text from a prompt.

        Args:
            prompt: The user prompt/input text.
            system: Optional system message.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds. If None, uses provider default.

        Returns:
            GenerationResult with generated text and metadata.

        Raises:
            ProviderError: On API errors or rate limits.
        """
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the provider's tokenizer.

        Args:
            text: Text to count tokens for.

        Returns:
            Token count.
        """
        ...

    def generate_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: float | None = None,
    ) -> GenerationResult:
        """
        Generate text from a multi-turn conversation.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Roles: 'system', 'user', 'assistant'
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds. If None, uses provider default.

        Returns:
            GenerationResult with generated text and metadata.

        Raises:
            ProviderError: On API errors or rate limits.
        """
        # Default implementation: concatenate conversation into a single prompt.
        # Subclasses should override for proper multi-turn support via the API.
        system = None
        parts: list[str] = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "user":
                parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                parts.append(f"Assistant: {msg['content']}")

        prompt = "\n\n".join(parts) if parts else ""

        return self.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate the cost for a generation call.

        Override in subclasses with actual pricing.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.

        Returns:
            Estimated cost in USD.
        """
        return 0.0


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class RateLimitError(ProviderError):
    """Raised when rate limited by the provider."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""

    pass


class ContextLengthError(ProviderError):
    """Raised when input exceeds context window."""

    def __init__(self, message: str, max_tokens: int | None = None):
        super().__init__(message)
        self.max_tokens = max_tokens
