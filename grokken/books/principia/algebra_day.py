"""
Handler for "An Introduction to Algebra" by Jeremiah Day (1847).

A mathematics textbook, being the first part of a course of mathematics.

Score: 37.4
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class AlgebraDay(BookProcessor):
    """
    Processor for An Introduction to Algebra.
    """

    barcode = "32044097009690"
    title = "An Introduction to Algebra"
    author = "Day, Jeremiah"
    date = "1847"

    notes = """
    Mathematics textbook on algebra.

    Known quirks:
    - Mathematical notation and equations
    - Problem numbers (Prob. 26, etc.)
    - Variables (x, y) that might confuse OCR
    - Running headers like "EQUATIONS"
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1847 text
        ocr.fix_digit_letter_confusion,  # Important for math variables (x, l, 0, o)
        ocr.remove_ocr_artifacts,
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Introduction to Algebra."""
        import regex as re

        # Remove running headers
        text = re.sub(
            r"^\s*\d+\s+EQUATIONS\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*EQUATIONS\.?\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
