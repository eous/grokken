"""
Data schemas for the generation pipeline.

These models represent the structured output of summarization
and Q&A generation.
"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field


def _utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class Segment(BaseModel):
    """A segment of a book (typically a chapter or section)."""

    index: int = Field(description="Zero-based segment index")
    title: str = Field(default="", description="Chapter/section title if detected")
    start_char: int = Field(description="Starting character position in source text")
    end_char: int = Field(description="Ending character position in source text")
    token_count: int = Field(description="Estimated token count for this segment")

    @computed_field
    @property
    def char_count(self) -> int:
        """Character count for this segment."""
        return self.end_char - self.start_char


class QATurn(BaseModel):
    """A follow-up Q&A turn with full conversation for training data."""

    question: str = Field(description="The question about the book content")
    answer: str = Field(description="The answer based on the summary")
    turn_number: int = Field(description="One-based turn number")
    style: str = Field(
        default="comprehension",
        description=(
            "Question style (comprehension, analysis, synthesis,"
            " evaluation, application, clarification)"
        ),
    )

    # Full prompts for training data reconstruction
    question_system_prompt: str = Field(
        default="", description="System prompt for question generation"
    )
    question_user_prompt: str = Field(default="", description="User prompt for question generation")
    answer_system_prompt: str = Field(default="", description="System prompt for answer generation")
    answer_user_prompt: str = Field(default="", description="User prompt for answer generation")

    def to_question_conversation(self) -> list[dict]:
        """Convert question generation to OpenAI conversation format."""
        return [
            {"role": "system", "content": self.question_system_prompt},
            {"role": "user", "content": self.question_user_prompt},
            {"role": "assistant", "content": self.question},
        ]

    def to_answer_conversation(self) -> list[dict]:
        """Convert answer generation to OpenAI conversation format."""
        return [
            {"role": "system", "content": self.answer_system_prompt},
            {"role": "user", "content": self.answer_user_prompt},
            {"role": "assistant", "content": self.answer},
        ]


class SegmentSummary(BaseModel):
    """Summary of a single segment with full conversation for training data."""

    segment_index: int = Field(description="Index of the segment summarized")
    segment_title: str = Field(default="", description="Title of the segment")

    # Full conversation for training data reconstruction
    system_prompt: str = Field(default="", description="System message sent to model")
    user_prompt: str = Field(default="", description="User message (segment + context)")
    summary: str = Field(description="Generated summary text (assistant response)")

    # Token counts
    input_tokens: int = Field(description="Tokens in input (segment + context)")
    output_tokens: int = Field(description="Tokens in generated summary")

    # Model metadata
    model: str = Field(description="Model used for generation")
    timestamp: datetime = Field(default_factory=_utc_now)

    def to_conversation(self) -> list[dict]:
        """Convert to OpenAI conversation format for training."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
            {"role": "assistant", "content": self.summary},
        ]


class BookSummaryRecord(BaseModel):
    """Complete summarization record for one book."""

    # Book metadata
    barcode: str = Field(description="HathiTrust barcode identifier")
    title: str = Field(description="Book title")
    author: str = Field(description="Book author")
    date: str = Field(default="", description="Publication date")

    # Strategy used
    strategy: Literal["short_book", "long_book"] = Field(
        description="Summarization strategy used"
    )

    # Segmentation (for long books)
    segments: list[Segment] = Field(
        default_factory=list,
        description="Book segments (chapters/sections)",
    )
    segment_summaries: list[SegmentSummary] = Field(
        default_factory=list,
        description="Progressive summaries for each segment",
    )

    # Final outputs
    final_summary: str = Field(
        default="",
        description="Final comprehensive summary",
    )
    qa_turns: list[QATurn] = Field(
        default_factory=list,
        description="Legacy single-turn Q&A (deprecated, use qa_conversation)",
    )
    qa_conversation: list[dict] = Field(
        default_factory=list,
        description="Multi-turn Q&A conversation as list of {role, content} messages",
    )

    # Generation metadata
    source_tokens: int = Field(description="Total tokens in source text")
    final_context_tokens: int = Field(
        default=0,
        description="Tokens in final generation context",
    )
    model: str = Field(description="Primary model used")
    timestamp: datetime = Field(default_factory=_utc_now)

    # Status for checkpointing
    status: Literal["pending", "segmenting", "summarizing", "qa_generation", "complete"] = Field(
        default="pending",
        description="Current processing status",
    )
    current_segment: int = Field(
        default=0,
        description="Current segment being processed (for resume)",
    )

    @computed_field
    @property
    def compression_ratio(self) -> float:
        """
        Ratio of source tokens to final summary tokens.

        Note: Uses approximate 4 chars/token for summary estimation since
        accurate tokenization would require model context. This provides
        a rough indicator of compression achieved.
        """
        if not self.final_summary:
            return 0.0
        # Approximate: ~4 characters per token for English text
        summary_tokens_approx = len(self.final_summary) // 4
        if summary_tokens_approx == 0:
            return 0.0
        return round(self.source_tokens / summary_tokens_approx, 2)

    def get_accumulated_summaries(self) -> str:
        """Get all segment summaries concatenated."""
        return "\n\n---\n\n".join(s.summary for s in self.segment_summaries)

    def to_training_record(self) -> dict:
        """
        Convert to a training data record.

        Returns a dict suitable for JSONL output with:
        - Book metadata
        - All segment summaries with full conversations
        - Final summary
        - Q&A turns with full conversations
        """
        return {
            "barcode": self.barcode,
            "title": self.title,
            "author": self.author,
            "date": self.date,
            "strategy": self.strategy,
            "source_tokens": self.source_tokens,
            "final_context_tokens": self.final_context_tokens,
            "compression_ratio": self.compression_ratio,
            # Segment summaries with full conversations for training
            "segment_conversations": [
                seg.to_conversation() for seg in self.segment_summaries
            ],
            "summary": self.final_summary,
            # Multi-turn Q&A conversation (primary format for training)
            "qa_conversation": self.qa_conversation,
            # Legacy single-turn Q&A (deprecated)
            "qa_turns": [turn.model_dump() for turn in self.qa_turns] if self.qa_turns else [],
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
        }


class Checkpoint(BaseModel):
    """Checkpoint for resuming interrupted generation."""

    config_name: str = Field(description="Name of the generation config")
    barcode: str = Field(description="Book being processed")
    record: BookSummaryRecord = Field(description="Current state of the record")
    timestamp: datetime = Field(default_factory=_utc_now)

    @classmethod
    def from_record(cls, config_name: str, record: BookSummaryRecord) -> "Checkpoint":
        """Create a checkpoint from a record."""
        return cls(
            config_name=config_name,
            barcode=record.barcode,
            record=record,
        )
