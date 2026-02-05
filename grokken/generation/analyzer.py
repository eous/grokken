"""
Book analysis for determining generation strategy.

Analyzes book text to determine token count and select the
appropriate summarization strategy (short vs long book).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
from openai_harmony import HarmonyEncodingName, load_harmony_encoding

from grokken.generation.config import StrategyConfig


@dataclass
class BookAnalysis:
    """Analysis results for a single book."""

    barcode: str
    title: str
    author: str
    date: str
    char_count: int
    token_count: int
    strategy: Literal["short_book", "long_book"]
    estimated_segments: int


class BookAnalyzer:
    """
    Analyzes books to determine processing strategy.

    Uses tiktoken for accurate token counting with GPT models.
    """

    # Minimum text length to consider valid (in characters)
    MIN_TEXT_LENGTH = 100

    def __init__(
        self,
        strategy_config: StrategyConfig | None = None,
        model: str = "gpt-5.2",
    ):
        """
        Initialize the analyzer.

        Args:
            strategy_config: Strategy configuration with thresholds.
            model: Model name for tokenization (default: gpt-5.2).
        """
        self.config = strategy_config or StrategyConfig()
        self._model = model
        self._encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using openai-harmony tokenizer.

        Args:
            text: Text to count tokens for.

        Returns:
            Token count.
        """
        return len(self._encoding.encode(text))

    def estimate_segments(self, token_count: int) -> int:
        """
        Estimate number of segments needed for a long book.

        Uses the segment summary token budget to calculate
        how many segments can fit in the final context window.

        Args:
            token_count: Total token count of the book.

        Returns:
            Estimated number of segments.
        """
        if token_count <= self.config.short_book_threshold:
            return 1

        # Reserve space for final segment and summaries
        available_for_summaries = self.config.max_context_tokens - (
            self.config.max_context_tokens // 4  # Reserve for final segment
        )
        max_segments = available_for_summaries // self.config.segment_summary_tokens

        # Estimate based on token count
        tokens_per_segment = token_count // max_segments
        # Ensure reasonable segment sizes (at least 10k tokens)
        min_tokens_per_segment = 10000
        estimated = max(1, token_count // max(tokens_per_segment, min_tokens_per_segment))

        return min(estimated, max_segments)

    def analyze(
        self,
        text: str,
        barcode: str,
        title: str = "",
        author: str = "",
        date: str = "",
    ) -> BookAnalysis:
        """
        Analyze a book to determine processing strategy.

        Args:
            text: Full book text.
            barcode: Book barcode identifier.
            title: Book title.
            author: Book author.
            date: Publication date.

        Returns:
            BookAnalysis with strategy determination.

        Raises:
            ValueError: If text is empty or too short.
        """
        if not text or not text.strip():
            raise ValueError(f"Empty text provided for barcode {barcode}")

        char_count = len(text)
        if char_count < self.MIN_TEXT_LENGTH:
            raise ValueError(
                f"Text too short for barcode {barcode}: {char_count} characters "
                f"(minimum: {self.MIN_TEXT_LENGTH})"
            )

        token_count = self.count_tokens(text)

        if token_count < self.config.short_book_threshold:
            strategy = "short_book"
            estimated_segments = 1
        else:
            strategy = "long_book"
            estimated_segments = self.estimate_segments(token_count)

        return BookAnalysis(
            barcode=barcode,
            title=title,
            author=author,
            date=date,
            char_count=char_count,
            token_count=token_count,
            strategy=strategy,
            estimated_segments=estimated_segments,
        )

    def analyze_from_dataframe(
        self,
        df: pd.DataFrame,
        barcode: str,
    ) -> BookAnalysis:
        """
        Analyze a book from a DataFrame.

        Args:
            df: DataFrame with 'barcode', 'text', 'title', 'author' columns.
            barcode: Barcode to look up.

        Returns:
            BookAnalysis for the specified book.

        Raises:
            ValueError: If barcode not found.
        """
        matches = df[df["barcode"] == barcode]
        if len(matches) == 0:
            raise ValueError(f"Barcode {barcode} not found in DataFrame")

        row = matches.iloc[0]
        return self.analyze(
            text=row["text"],
            barcode=barcode,
            title=row.get("title", ""),
            author=row.get("author", ""),
            date=str(row.get("date", "")),
        )

    def analyze_from_parquet(
        self,
        path: str | Path,
        barcode: str,
    ) -> BookAnalysis:
        """
        Analyze a book from a parquet file.

        Args:
            path: Path to parquet file.
            barcode: Barcode to look up.

        Returns:
            BookAnalysis for the specified book.
        """
        df = pd.read_parquet(path)
        return self.analyze_from_dataframe(df, barcode)

    def analyze_collection(
        self,
        df: pd.DataFrame,
        barcodes: list[str] | None = None,
    ) -> list[BookAnalysis]:
        """
        Analyze multiple books from a DataFrame.

        Args:
            df: DataFrame with book data.
            barcodes: Optional list of barcodes to analyze.
                     If None, analyzes all books in DataFrame.

        Returns:
            List of BookAnalysis objects.
        """
        if barcodes is None:
            barcodes = df["barcode"].unique().tolist()

        analyses = []
        for barcode in barcodes:
            try:
                analysis = self.analyze_from_dataframe(df, barcode)
                analyses.append(analysis)
            except ValueError:
                # Skip missing barcodes
                continue

        return analyses
