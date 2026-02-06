"""
Configuration models for the generation pipeline.

Uses Pydantic for validation and YAML for configuration files.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategyConfig(BaseModel):
    """Configuration for summarization strategy."""

    max_context_tokens: int = Field(
        default=131000,
        description="Maximum tokens for final context window",
    )
    segment_summary_tokens: int = Field(
        default=8000,
        description="Target tokens per segment summary",
    )
    final_summary_tokens: int = Field(
        default=16000,
        description="Target tokens for final summary",
    )
    qa_turns: int = Field(
        default=5,
        description="Number of Q&A turns to generate",
    )
    short_book_threshold: int = Field(
        default=131000,
        description="Token threshold below which to use short book strategy",
    )


class ProviderConfig(BaseModel):
    """Configuration for LLM provider."""

    model_config = ConfigDict(extra="forbid")

    name: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="Provider name",
    )
    model: str = Field(
        default="gpt-5.2",
        description="Model identifier",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=128000,
        description="Maximum tokens in response",
    )
    timeout: float = Field(
        default=300.0,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts",
    )


class GenerationConfig(BaseModel):
    """Complete configuration for a generation run."""

    name: str = Field(
        description="Name for this generation run",
    )
    source_parquet: Path = Field(
        description="Path to source parquet file with processed text",
    )
    barcode: str | None = Field(
        default=None,
        description="Single book barcode to process",
    )
    collection: str | None = Field(
        default=None,
        description="Collection name to process all books",
    )
    strategy: StrategyConfig = Field(
        default_factory=StrategyConfig,
        description="Summarization strategy configuration",
    )
    provider: ProviderConfig = Field(
        default_factory=ProviderConfig,
        description="LLM provider configuration",
    )
    output_dir: Path = Field(
        description="Directory for output files",
    )
    checkpoint_every: int = Field(
        default=1,
        description="Checkpoint after every N segments",
    )
    resume_from: str | None = Field(
        default=None,
        description="Resume from a checkpoint file",
    )

    @field_validator("source_parquet", "output_dir", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        """Convert string paths to Path objects."""
        return Path(v)

    def model_post_init(self, __context) -> None:
        """Validate that either barcode or collection is specified."""
        if not self.barcode and not self.collection:
            raise ValueError("Must specify either 'barcode' or 'collection'")


def load_config(path: str | Path) -> GenerationConfig:
    """
    Load configuration from a YAML file.

    Args:
        path: Path to YAML configuration file.

    Returns:
        Validated GenerationConfig object.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValidationError: If config is invalid.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return GenerationConfig(**data)


def save_config(config: GenerationConfig, path: str | Path) -> None:
    """
    Save configuration to a YAML file.

    Args:
        config: Configuration to save.
        path: Output path for YAML file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict, handling Path objects
    data = config.model_dump(mode="json")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
