"""
Handler for "Principles of Political Economy" by John Stuart Mill (1884 edition).

Mill's foundational work on economics, first published in 1848.
This is the 1884 edition.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class PoliticalEconomyMill1884(BookProcessor):
    """
    Processor for Principles of Political Economy (Mill, 1884).
    """

    barcode = "LI3QQB"
    title = "Principles of Political Economy"
    author = "Mill, John Stuart"
    date = "1884"

    notes = """
    Mill's classic work on political economy.

    Known quirks:
    - Running headers with Book/Chapter markers (BOOK IV. CHAPTER IV. §3.)
    - Economic theory and philosophy
    - Dense argumentative prose
    - Footnotes with references
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Principles of Political Economy (Mill)."""
        import regex as re

        # Remove running headers with Book/Chapter markers
        text = re.sub(
            r"^\s*BOOK\s+[IVXLC]+\.\s+CHAPTER\s+[IVXLC]+\.\s*§?\d*\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        # Remove single letters on their own lines (OCR artifacts)
        text = re.sub(r"^\s*[A-Z]\s*$", "", text, flags=re.MULTILINE)

        return text
