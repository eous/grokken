"""
Core generation logic for training data pipeline.

Orchestrates the complete workflow from book text to
summarization and Q&A generation.
"""

import json
import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from grokken.generation.analyzer import BookAnalyzer
from grokken.generation.books import get_handler
from grokken.generation.config import GenerationConfig
from grokken.generation.prompts import (
    format_final_summary_prompt,
    format_segment_prompt,
    format_short_book_prompt,
)
from grokken.generation.providers.base import LLMProvider
from grokken.generation.providers.openai import create_provider
from grokken.generation.schema import (
    BookSummaryRecord,
    Checkpoint,
    SegmentSummary,
)
from grokken.generation.segmenter import Segmenter
from grokken.generation.simulated_user import SimulatedUser

logger = logging.getLogger(__name__)


class PipelineResult:
    """Result of a generation run, including success/failure tracking."""

    def __init__(self):
        self.records: list[BookSummaryRecord] = []
        self.failed_books: list[dict] = []
        self.total_cost: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def add_success(self, record: BookSummaryRecord) -> None:
        """Add a successfully processed book."""
        self.records.append(record)

    def add_failure(self, barcode: str, error: str) -> None:
        """Track a failed book."""
        self.failed_books.append({"barcode": barcode, "error": error})

    def add_cost(self, input_tokens: int, output_tokens: int, cost: float) -> None:
        """Accumulate cost from a generation call."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

    @property
    def success_count(self) -> int:
        return len(self.records)

    @property
    def failure_count(self) -> int:
        return len(self.failed_books)


class Generator:
    """
    Orchestrates the generation pipeline for book summarization.

    Handles both short books (single-pass) and long books (progressive).
    """

    def __init__(
        self,
        config: GenerationConfig,
        provider: LLMProvider | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ):
        """
        Initialize the generator.

        Args:
            config: Generation configuration.
            provider: LLM provider. If None, creates from config.
            progress_callback: Optional callback for progress updates.
                              Called as callback(message, current, total).
        """
        self.config = config
        self.provider = provider or create_provider(config.provider)
        self.analyzer = BookAnalyzer(config.strategy, model=config.provider.model)
        self.segmenter = Segmenter(config.strategy, model=config.provider.model)
        self.simulated_user = SimulatedUser(self.provider)
        self.progress_callback = progress_callback

        # Cost tracking
        self._generation_result = PipelineResult()

        # Cached source DataFrame (loaded on first access)
        self._source_df: pd.DataFrame | None = None

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def _progress(self, message: str, current: int = 0, total: int = 0) -> None:
        """Report progress."""
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message, current, total)

    def _track_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Track cost from a generation call and return the cost."""
        cost = self.provider.estimate_cost(input_tokens, output_tokens)
        self._generation_result.add_cost(input_tokens, output_tokens, cost)
        return cost

    def load_book_text(self, barcode: str) -> tuple[str, dict]:
        """
        Load book text and metadata from source parquet.

        Returns:
            Tuple of (text, metadata_dict)
        """
        if self._source_df is None:
            self._source_df = pd.read_parquet(self.config.source_parquet)
        matches = self._source_df[self._source_df["barcode"] == barcode]

        if len(matches) == 0:
            raise ValueError(f"Barcode {barcode} not found in {self.config.source_parquet}")

        row = matches.iloc[0]
        text = row["text"]
        metadata = {
            "barcode": barcode,
            "title": row.get("title", ""),
            "author": row.get("author", ""),
            "date": str(row.get("date", "")),
        }
        return text, metadata

    def process_short_book(
        self,
        text: str,
        metadata: dict,
        token_count: int,
    ) -> BookSummaryRecord:
        """
        Process a short book with single-pass summarization.
        """
        self._progress(f"Processing short book: {metadata['title']}")

        # Create record
        record = BookSummaryRecord(
            barcode=metadata["barcode"],
            title=metadata["title"],
            author=metadata["author"],
            date=metadata["date"],
            strategy="short_book",
            source_tokens=token_count,
            model=self.provider.model_name,
            status="summarizing",
        )

        # Generate summary
        self._progress("Generating summary...")
        system, prompt = format_short_book_prompt(
            title=metadata["title"],
            author=metadata["author"],
            date=metadata["date"],
            text=text,
            token_count=token_count,
            target_tokens=self.config.strategy.final_summary_tokens,
        )

        result = self.provider.generate(
            prompt=prompt,
            system=system,
            temperature=self.config.provider.temperature,
            max_tokens=self.config.provider.max_tokens,
        )
        cost = self._track_cost(result.input_tokens, result.output_tokens)
        self._progress(f"Summary generated (cost: ${cost:.4f})")

        record.final_summary = result.text
        record.final_context_tokens = result.input_tokens
        self._save_checkpoint(record)

        # Generate Q&A
        self._progress("Generating Q&A turns...")
        record = self._generate_qa(record)
        self._save_checkpoint(record)

        record.status = "complete"
        record.timestamp = datetime.now(UTC)

        return record

    def process_long_book(
        self,
        text: str,
        metadata: dict,
        token_count: int,
        resume_record: BookSummaryRecord | None = None,
    ) -> BookSummaryRecord:
        """
        Process a long book with progressive segmentation and summarization.
        """
        self._progress(f"Processing long book: {metadata['title']}")

        # Initialize or resume record
        if resume_record:
            record = resume_record
            self._progress(f"Resuming from segment {record.current_segment}")
        else:
            record = BookSummaryRecord(
                barcode=metadata["barcode"],
                title=metadata["title"],
                author=metadata["author"],
                date=metadata["date"],
                strategy="long_book",
                source_tokens=token_count,
                model=self.provider.model_name,
                status="segmenting",
            )

        # Segment the book if not already done
        if not record.segments:
            self._progress("Segmenting book...")

            # Check for per-book handler with custom segmentation
            handler = get_handler(metadata["barcode"])
            if handler:
                self._progress(f"Using custom handler for {metadata['barcode']}")
                record.segments = handler.get_segments(text)
                method = "custom_handler"
            else:
                seg_result = self.segmenter.segment(text)
                record.segments = seg_result.segments
                method = seg_result.method

            self._progress(f"Created {len(record.segments)} segments using {method} method")

        record.status = "summarizing"
        total_segments = len(record.segments)

        # Process each segment
        for i in range(record.current_segment, total_segments):
            segment = record.segments[i]
            self._progress(
                f"Summarizing segment {i + 1}/{total_segments}: {segment.title}",
                i + 1,
                total_segments,
            )

            # Get accumulated summaries
            accumulated = record.get_accumulated_summaries() if record.segment_summaries else None

            # Get segment text
            segment_text = self.segmenter.get_segment_text(text, segment)

            # Generate segment summary
            system, prompt = format_segment_prompt(
                title=metadata["title"],
                author=metadata["author"],
                segment_index=i,
                total_segments=total_segments,
                segment_title=segment.title,
                segment_text=segment_text,
                accumulated_summaries=accumulated,
                target_tokens=self.config.strategy.segment_summary_tokens,
            )

            result = self.provider.generate(
                prompt=prompt,
                system=system,
                temperature=self.config.provider.temperature,
                max_tokens=self.config.provider.max_tokens,
            )
            cost = self._track_cost(result.input_tokens, result.output_tokens)
            self._progress(f"Segment {i + 1} summarized (cost: ${cost:.4f})")

            # Store segment summary with full conversation for training data
            segment_summary = SegmentSummary(
                segment_index=i,
                segment_title=segment.title,
                system_prompt=system,
                user_prompt=prompt,
                summary=result.text,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                model=result.model,
            )
            record.segment_summaries.append(segment_summary)
            record.current_segment = i + 1

            # Generate per-segment Q&A (with pressure valve)
            self._generate_segment_qa(record, segment_summary)

            # Checkpoint if configured
            if self.config.checkpoint_every and (i + 1) % self.config.checkpoint_every == 0:
                self._save_checkpoint(record)

        # Checkpoint after all segments complete (before final summary)
        self._save_checkpoint(record)

        # Generate final summary from accumulated summaries
        self._progress("Generating final summary...")
        accumulated = record.get_accumulated_summaries()

        system, prompt = format_final_summary_prompt(
            title=metadata["title"],
            author=metadata["author"],
            date=metadata["date"],
            accumulated_summaries=accumulated,
            num_segments=total_segments,
            target_tokens=self.config.strategy.final_summary_tokens,
        )

        result = self.provider.generate(
            prompt=prompt,
            system=system,
            temperature=self.config.provider.temperature,
            max_tokens=self.config.provider.max_tokens,
        )
        cost = self._track_cost(result.input_tokens, result.output_tokens)
        self._progress(f"Final summary generated (cost: ${cost:.4f})")

        record.final_summary = result.text
        record.final_context_tokens = result.input_tokens
        self._save_checkpoint(record)

        # Generate Q&A
        self._progress("Generating Q&A turns...")
        record = self._generate_qa(record)
        self._save_checkpoint(record)

        record.status = "complete"
        record.timestamp = datetime.now(UTC)

        return record

    # Threshold in tokens above which per-segment QA is skipped.
    # Segments near 100K tokens leave little room for QA in a 131K training sample.
    SEGMENT_QA_TOKEN_THRESHOLD = 105_000

    def _generate_segment_qa(
        self,
        record: BookSummaryRecord,
        segment_summary: SegmentSummary,
    ) -> None:
        """
        Generate per-segment Q&A turns for a single segment summary.

        Skips generation if the segment's summarization conversation already
        exceeds SEGMENT_QA_TOKEN_THRESHOLD tokens (pressure valve to keep
        training samples under 131K seq len).
        """
        seg_tokens = segment_summary.input_tokens + segment_summary.output_tokens
        if seg_tokens >= self.SEGMENT_QA_TOKEN_THRESHOLD:
            logger.info(
                f"Skipping per-segment QA for '{segment_summary.segment_title}' "
                f"({seg_tokens:,} tokens >= {self.SEGMENT_QA_TOKEN_THRESHOLD:,} threshold)"
            )
            record.segment_qa_conversations.append([])
            return

        # Use generate_multiturn_qa with a single segment so each answer
        # sees the full conversation history (not independent single-turn calls).
        conversation = self.simulated_user.generate_multiturn_qa(
            title=record.title,
            author=record.author,
            segment_summaries=[
                {
                    "title": segment_summary.segment_title,
                    "summary": segment_summary.summary,
                }
            ],
            turns_per_segment=5,
            temperature=self.config.provider.temperature,
        )

        num_turns = sum(1 for m in conversation if m.get("role") == "assistant")
        self._progress(
            f"Segment '{segment_summary.segment_title}' QA: {num_turns} turns "
            f"(seg was {seg_tokens:,} tokens)"
        )
        record.segment_qa_conversations.append(conversation)

    def _generate_qa(self, record: BookSummaryRecord) -> BookSummaryRecord:
        """Generate multi-turn Q&A conversation from segment summaries."""
        record.status = "qa_generation"

        # Build segment summaries list for multi-turn Q&A
        segment_summaries = [
            {"title": seg.segment_title, "summary": seg.summary} for seg in record.segment_summaries
        ]

        # If no segment summaries (short book), use final summary as single segment
        if not segment_summaries and record.final_summary:
            segment_summaries = [{"title": record.title, "summary": record.final_summary}]

        # Generate multi-turn conversation
        num_summaries = max(1, len(segment_summaries))
        turns_per_seg = max(1, self.config.strategy.qa_turns // num_summaries)
        qa_conversation = self.simulated_user.generate_multiturn_qa(
            title=record.title,
            author=record.author,
            segment_summaries=segment_summaries,
            turns_per_segment=turns_per_seg,
            temperature=self.config.provider.temperature,
        )

        record.qa_conversation = qa_conversation

        # Count actual Q&A turns (user messages after system message)
        num_turns = sum(1 for msg in qa_conversation if msg.get("role") == "user")
        self._progress(
            f"Generated multi-turn Q&A: {len(qa_conversation)} messages ({num_turns} turns)"
        )

        return record

    def _save_checkpoint(self, record: BookSummaryRecord) -> Path:
        """Save a checkpoint for resuming using atomic write."""
        checkpoint = Checkpoint.from_record(self.config.name, record)
        # Use consistent filename (overwrites previous checkpoint for this book)
        checkpoint_path = self.config.output_dir / f"checkpoint_{record.barcode}.json"

        # Atomic write: write to temp file then rename
        temp_path = checkpoint_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(checkpoint.model_dump_json(indent=2))
        os.replace(temp_path, checkpoint_path)

        self._progress(f"Checkpoint saved: {checkpoint_path} (segment {record.current_segment})")
        return checkpoint_path

    def _load_checkpoint(self, path: str | Path) -> BookSummaryRecord:
        """Load a checkpoint for resuming."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        checkpoint = Checkpoint(**data)
        return checkpoint.record

    def _cleanup_checkpoint(self, barcode: str) -> None:
        """Remove checkpoint file after successful completion."""
        checkpoint_path = self.config.output_dir / f"checkpoint_{barcode}.json"
        if checkpoint_path.exists():
            checkpoint_path.unlink()
            self._progress(f"Cleaned up checkpoint: {checkpoint_path}")

    def process_book(self, barcode: str) -> BookSummaryRecord:
        """
        Process a single book through the full pipeline.

        Automatically selects short or long book strategy.

        Raises:
            ValueError: If checkpoint strategy doesn't match analyzed strategy.
        """
        # Check for resume
        resume_record = None
        if self.config.resume_from:
            resume_record = self._load_checkpoint(self.config.resume_from)
            self._progress(f"Resuming from checkpoint: {self.config.resume_from}")

        # Load book
        text, metadata = self.load_book_text(barcode)

        # Analyze to determine strategy
        analysis = self.analyzer.analyze(
            text=text,
            barcode=barcode,
            title=metadata["title"],
            author=metadata["author"],
            date=metadata["date"],
        )

        self._progress(
            f"Book analysis: {analysis.token_count:,} tokens, strategy={analysis.strategy}"
        )

        # Validate checkpoint strategy matches if resuming
        if resume_record:
            if resume_record.strategy != analysis.strategy:
                raise ValueError(
                    f"Checkpoint strategy '{resume_record.strategy}' does not match "
                    f"analyzed strategy '{analysis.strategy}' for barcode {barcode}. "
                    f"This may indicate config changes since the checkpoint was created."
                )
            if resume_record.barcode != barcode:
                raise ValueError(
                    f"Checkpoint barcode '{resume_record.barcode}' does not match "
                    f"requested barcode '{barcode}'."
                )

        # Process based on strategy
        if analysis.strategy == "short_book":
            if resume_record:
                logger.warning(
                    f"Ignoring checkpoint for short book {barcode} - "
                    "short books are processed in a single pass"
                )
            record = self.process_short_book(text, metadata, analysis.token_count)
        else:
            record = self.process_long_book(text, metadata, analysis.token_count, resume_record)

        # Save result
        output_path = self.config.output_dir / f"{barcode}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))

        # Clean up checkpoint after successful completion
        self._cleanup_checkpoint(barcode)

        self._progress(f"Saved result to {output_path}")

        return record

    def run(self) -> "PipelineResult":
        """
        Run the generation pipeline for configured books.

        Returns:
            PipelineResult with processed records, failures, and cost tracking.
        """
        # Reset generation result for this run
        self._generation_result = PipelineResult()

        if self.config.barcode:
            # Single book
            try:
                record = self.process_book(self.config.barcode)
                self._generation_result.add_success(record)
            except Exception as e:
                logger.error(f"Error processing {self.config.barcode}: {e}")
                self._generation_result.add_failure(self.config.barcode, str(e))

        elif self.config.collection:
            # Process collection
            from grokken.registry import registry

            processors = registry.get_collection(self.config.collection)
            barcodes = [p.barcode for p in processors]

            self._progress(f"Processing collection {self.config.collection}: {len(barcodes)} books")

            for i, barcode in enumerate(barcodes):
                self._progress(f"Book {i + 1}/{len(barcodes)}: {barcode}")
                try:
                    record = self.process_book(barcode)
                    self._generation_result.add_success(record)
                except Exception as e:
                    logger.error(f"Error processing {barcode}: {e}")
                    self._generation_result.add_failure(barcode, str(e))
                    continue

        result = self._generation_result

        # Save combined JSONL output
        if result.records:
            jsonl_path = self.config.output_dir / "training_data.jsonl"
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for record in result.records:
                    f.write(json.dumps(record.to_training_record()) + "\n")
            self._progress(f"Saved training data to {jsonl_path}")

        # Save failed books report if any failures
        if result.failed_books:
            failures_path = self.config.output_dir / "failed_books.json"
            with open(failures_path, "w", encoding="utf-8") as f:
                json.dump(result.failed_books, f, indent=2)
            self._progress(f"Saved failure report to {failures_path}")
            logger.warning(
                f"{result.failure_count} books failed to process. See {failures_path} for details."
            )

        # Log cost summary
        self._progress(
            f"Generation complete: {result.success_count} succeeded, "
            f"{result.failure_count} failed, "
            f"total cost: ${result.total_cost:.4f}"
        )

        return result
