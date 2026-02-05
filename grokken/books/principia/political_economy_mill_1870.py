"""
Handler for "Principles of Political Economy" by John Stuart Mill (1870 edition).

An alternate edition of Mill's foundational work on economics.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class PoliticalEconomyMill1870(BookProcessor):
    """
    Processor for Principles of Political Economy (Mill, 1870).
    """

    barcode = "HXQ9SJ"
    title = "Principles of Political Economy, with some of their applications to social philosophy"
    author = "Mill, John Stuart"
    date = "1870"

    notes = """
    Earlier edition of Mill's political economy work.

    Known quirks:
    - Similar to 1884 edition
    - Running headers with Book/Chapter markers
    - Economic theory and philosophy
    - Dense argumentative prose
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
        """Book-specific cleanup for Principles of Political Economy (Mill 1870)."""
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
