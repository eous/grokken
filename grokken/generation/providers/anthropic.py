"""
Anthropic provider implementation.

Supports Claude Opus, Sonnet, and Haiku models.
"""

import logging
import os
import random
import time

from anthropic import Anthropic
from anthropic import APIError as AnthropicAPIError
from anthropic import AuthenticationError as AnthropicAuthError
from anthropic import RateLimitError as AnthropicRateLimitError

from grokken.generation.config import ProviderConfig
from grokken.generation.providers.base import (
    AuthenticationError,
    ContextLengthError,
    GenerationResult,
    LLMProvider,
    ProviderError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (update as needed)
MODEL_PRICING = {
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}


class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider.

    Uses the official Anthropic Python client with manual retry
    handling and exponential backoff.
    """

    def __init__(
        self,
        config: ProviderConfig | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the Anthropic provider.

        Args:
            config: Provider configuration.
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.config = config or ProviderConfig(name="anthropic", model="claude-opus-4-6")

        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise AuthenticationError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self._client = Anthropic(
            api_key=api_key,
            max_retries=0,  # We handle retries ourselves
        )

    @property
    def model_name(self) -> str:
        """Return the model identifier."""
        return self.config.model

    def count_tokens(self, text: str) -> int:
        """Approximate token count using char/4 heuristic."""
        return len(text) // 4

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> GenerationResult:
        """
        Generate text using the Anthropic API.

        Builds a messages list from prompt/system and delegates to _call_api.

        Args:
            prompt: The user prompt/input text.
            system: Optional system message.
            temperature: Sampling temperature. If None, uses config default.
            max_tokens: Maximum tokens to generate. If None, uses config default.
            timeout: Request timeout in seconds. If None, uses config default.
        """
        messages = [{"role": "user", "content": prompt}]

        return self._call_api(
            messages=messages,
            system=system,
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

        Extracts system messages and ensures strict role alternation
        as required by the Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            temperature: Sampling temperature. If None, uses config default.
            max_tokens: Maximum tokens to generate. If None, uses config default.
            timeout: Request timeout in seconds. If None, uses config default.
        """
        # Extract system messages into a single system string
        system_parts: list[str] = []
        non_system: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
            else:
                non_system.append(msg)

        system = "\n\n".join(system_parts) if system_parts else None

        # Merge consecutive same-role messages (Anthropic requires strict alternation)
        merged: list[dict[str, str]] = []
        for msg in non_system:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1] = {
                    "role": msg["role"],
                    "content": merged[-1]["content"] + "\n\n" + msg["content"],
                }
            else:
                merged.append(msg)

        return self._call_api(
            messages=merged,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    def _call_api(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> GenerationResult:
        """
        Shared API call with retry logic.

        Handles Anthropic-specific API differences:
        - system is a top-level kwarg, not in messages
        - Temperature clamped to 1.0 (Anthropic max)
        - Response structure differs from OpenAI
        """
        if temperature is None:
            temperature = self.config.temperature
        if max_tokens is None:
            max_tokens = self.config.max_tokens
        if timeout is None:
            timeout = self.config.timeout

        # Anthropic max temperature is 1.0
        if temperature > 1.0:
            logger.debug("Clamping temperature from %.2f to 1.0 (Anthropic max)", temperature)
            temperature = 1.0

        kwargs: dict = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout,
        }
        if system:
            kwargs["system"] = system

        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self._client.messages.create(**kwargs)

                if not response.content:
                    raise ProviderError("API returned empty content list")

                result = GenerationResult(
                    text=response.content[0].text,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model=response.model,
                    finish_reason=response.stop_reason,
                )

                if response.stop_reason == "max_tokens":
                    logger.warning(
                        "Response truncated: hit max_tokens limit (%s). "
                        "Output may be incomplete (%d tokens generated).",
                        max_tokens,
                        response.usage.output_tokens,
                    )

                return result

            except AnthropicRateLimitError as e:
                last_error = e
                retry_after = self._get_retry_after(attempt)
                if attempt < self.config.max_retries:
                    time.sleep(retry_after)
                else:
                    raise RateLimitError(str(e), retry_after=retry_after) from e

            except AnthropicAuthError as e:
                raise AuthenticationError(str(e)) from e

            except AnthropicAPIError as e:
                error_str = str(e).lower()
                if (
                    "context" in error_str
                    or "too long" in error_str
                    or "too many input tokens" in error_str
                ):
                    raise ContextLengthError(str(e)) from e

                last_error = e
                if attempt < self.config.max_retries:
                    time.sleep(2**attempt)
                else:
                    raise ProviderError(str(e)) from e

        raise ProviderError(f"Max retries exceeded: {last_error}")

    def _get_retry_after(self, attempt: int) -> float:
        """
        Calculate exponential backoff with jitter.

        Uses jitter to avoid thundering herd when multiple clients retry.
        """
        base_delay = 2**attempt
        jittered = base_delay * (0.5 + random.random())  # noqa: S311
        return min(jittered, 60)  # Cap at 60 seconds

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost based on model pricing."""
        pricing = MODEL_PRICING.get(self.config.model, {"input": 15.0, "output": 75.0})

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
