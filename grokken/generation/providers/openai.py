"""
OpenAI provider implementation.

Supports GPT-4, GPT-4o, GPT-5.2, and other OpenAI models.
"""

import os
import random
import time

from openai import APIError, OpenAI
from openai import AuthenticationError as OpenAIAuthError
from openai import RateLimitError as OpenAIRateLimitError
from openai_harmony import HarmonyEncodingName, load_harmony_encoding

from grokken.generation.config import ProviderConfig
from grokken.generation.providers.base import (
    AuthenticationError,
    ContextLengthError,
    GenerationResult,
    LLMProvider,
    ProviderError,
    RateLimitError,
)

# Pricing per 1M tokens (update as needed)
MODEL_PRICING = {
    "gpt-5.2": {"input": 5.00, "output": 15.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
}


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider.

    Uses the official OpenAI Python client with automatic retry
    handling and exponential backoff.
    """

    def __init__(
        self,
        config: ProviderConfig | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the OpenAI provider.

        Args:
            config: Provider configuration.
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
        """
        self.config = config or ProviderConfig()

        # Get API key from param, config, or environment
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self._client = OpenAI(
            api_key=api_key,
            timeout=self.config.timeout,
            max_retries=0,  # We handle retries ourselves
        )
        self._encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return self.config.model

    def count_tokens(self, text: str) -> int:
        """Count tokens using openai-harmony tokenizer."""
        return len(self._encoding.encode(text))

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> GenerationResult:
        """
        Generate text using the OpenAI API.

        Builds a messages list from prompt/system and delegates to generate_chat.

        Args:
            prompt: The user prompt/input text.
            system: Optional system message.
            temperature: Sampling temperature. If None, uses config default.
            max_tokens: Maximum tokens to generate. If None, uses config default.
            timeout: Request timeout in seconds. If None, uses config default.
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return self.generate_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    def generate_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> GenerationResult:
        """
        Generate text from a multi-turn conversation.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature. If None, uses config default.
            max_tokens: Maximum tokens to generate. If None, uses config default.
            timeout: Request timeout in seconds. If None, uses config default.
        """
        if temperature is None:
            temperature = self.config.temperature
        if max_tokens is None:
            max_tokens = self.config.max_tokens
        if timeout is None:
            timeout = self.config.timeout

        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    timeout=timeout,
                )

                if not response.choices:
                    raise ProviderError("API returned empty choices list")

                choice = response.choices[0]
                usage = response.usage

                return GenerationResult(
                    text=choice.message.content or "",
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                    model=response.model,
                    finish_reason=choice.finish_reason,
                )

            except OpenAIRateLimitError as e:
                last_error = e
                retry_after = self._get_retry_after(e, attempt)
                if attempt < self.config.max_retries:
                    time.sleep(retry_after)
                else:
                    raise RateLimitError(str(e), retry_after=retry_after) from e

            except OpenAIAuthError as e:
                raise AuthenticationError(str(e)) from e

            except APIError as e:
                if "context_length" in str(e).lower() or "maximum context" in str(e).lower():
                    raise ContextLengthError(str(e)) from e

                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(2**attempt)
                else:
                    raise ProviderError(str(e)) from e

        raise ProviderError(f"Max retries exceeded: {last_error}")

    def _get_retry_after(self, error: OpenAIRateLimitError, attempt: int) -> float:
        """
        Get retry delay from rate limit error or calculate exponential backoff.

        Uses jitter to avoid thundering herd when multiple clients retry.
        """
        # Exponential backoff with jitter: base * (0.5 to 1.5)
        base_delay = 2**attempt
        jittered = base_delay * (0.5 + random.random())  # noqa: S311
        return min(jittered, 60)  # Cap at 60 seconds

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost based on model pricing.
        """
        pricing = MODEL_PRICING.get(self.config.model, {"input": 5.0, "output": 15.0})

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost


def create_provider(config: ProviderConfig) -> LLMProvider:
    """
    Factory function to create a provider from config.

    Args:
        config: Provider configuration.

    Returns:
        Configured LLMProvider instance.

    Raises:
        ValueError: If provider name is not supported.
    """
    if config.name == "openai":
        return OpenAIProvider(config)
    else:
        raise ValueError(f"Unsupported provider: {config.name}")
