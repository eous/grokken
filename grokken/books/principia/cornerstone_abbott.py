"""
Handler for "The Corner-stone" by Jacob Abbott (1830).

A familiar illustration of the principles of Christian truth.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class Cornerstone(BookProcessor):
    """
    Processor for The Corner-stone.
    """

    barcode = "AH45Q4"
    title = "The Corner-stone, or, A familiar illustration of Christian principles"
    author = "Abbott, Jacob"
    date = "1830"

    notes = """
    Religious/devotional work by Jacob Abbott (famous for Rollo books).

    Known quirks:
    - Religious/Christian content
    - Discussion of redemption, Jesus Christ
    - Devotional prose style
    - Early date (1830) may mean more OCR issues
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1830 text
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for The Corner-stone."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
