"""
Base class for book-specific processing.

Each book (or group of similar books) gets a handler that inherits from
BookProcessor and defines its specific transforms and quirks.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, ClassVar

import pandas as pd


# Type alias for transform functions
Transform = Callable[[str], str]


@dataclass
class BookProcessor:
    """
    Base class for book-specific text processing.

    Subclass this to handle specific books or book collections.
    Override `transforms` with a list of transform functions,
    and `post_process` for any book-specific final cleanup.

    Example:
        class PrinciplesPsychology(BookProcessor):
            barcode = "32044010149714"
            title = "The Principles of Psychology"

            transforms = [
                typography.fix_ligatures,
                whitespace.dehyphenate,
                structure.remove_page_headers(pattern=r"PSYCHOLOGY"),
            ]

            def post_process(self, text: str) -> str:
                # Handle James's Greek passages
                return self._transliterate_greek(text)
    """

    # Class-level attributes (override in subclass)
    barcode: ClassVar[str] = ""
    title: ClassVar[str] = ""
    author: ClassVar[str] = ""
    date: ClassVar[str] = ""
    notes: ClassVar[str] = ""  # Document quirks for future reference

    # Transforms to apply in order (override in subclass)
    transforms: ClassVar[list[Transform]] = []

    # Instance state
    _raw_text: str = field(default="", repr=False)
    _processed_text: str = field(default="", repr=False)

    def load_raw(self, source: Path | pd.DataFrame) -> str:
        """
        Load raw text from source.

        Args:
            source: Either a Path to a parquet file, or a DataFrame with
                   'barcode' and 'text' columns.

        Returns:
            Raw text content for this book.

        Raises:
            ValueError: If barcode not found in source.
        """
        if isinstance(source, (str, Path)):
            df = pd.read_parquet(source)
        else:
            df = source

        matches = df[df["barcode"] == self.barcode]
        if len(matches) == 0:
            raise ValueError(f"Barcode {self.barcode} not found in source")

        self._raw_text = matches.iloc[0]["text"]
        return self._raw_text

    def process(self, text: str | None = None) -> str:
        """
        Apply all transforms in sequence.

        Args:
            text: Text to process. If None, uses previously loaded raw text.

        Returns:
            Processed text after all transforms and post_process.
        """
        if text is None:
            text = self._raw_text

        if not text:
            raise ValueError("No text to process. Call load_raw() first or pass text.")

        # Apply transforms in order
        for transform in self.transforms:
            text = transform(text)

        # Apply book-specific post-processing
        text = self.post_process(text)

        self._processed_text = text
        return text

    def post_process(self, text: str) -> str:
        """
        Override for book-specific final cleanup.

        This runs after all standard transforms. Use for edge cases
        that don't fit into reusable transforms.

        Args:
            text: Text after standard transforms.

        Returns:
            Final processed text.
        """
        return text

    def run(self, source: Path | pd.DataFrame) -> str:
        """
        Full pipeline: load -> process -> return.

        Args:
            source: Path to parquet or DataFrame with source data.

        Returns:
            Fully processed text.
        """
        self.load_raw(source)
        return self.process()

    @property
    def raw_text(self) -> str:
        """The loaded raw text."""
        return self._raw_text

    @property
    def processed_text(self) -> str:
        """The processed text (after calling process())."""
        return self._processed_text

    def stats(self) -> dict:
        """Return statistics about the processing."""
        return {
            "barcode": self.barcode,
            "title": self.title,
            "raw_chars": len(self._raw_text),
            "processed_chars": len(self._processed_text),
            "reduction_pct": (
                round((1 - len(self._processed_text) / len(self._raw_text)) * 100, 2)
                if self._raw_text
                else 0
            ),
            "transforms_applied": len(self.transforms),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(barcode={self.barcode!r}, title={self.title[:50]!r}...)"
