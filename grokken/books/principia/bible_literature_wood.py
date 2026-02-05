"""
Handler for "The Bible as Literature" by Irving Francis Wood (1914).

An introduction to studying the Bible as a literary work.

Score: 36.8
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class BibleAsLiterature(BookProcessor):
    """
    Processor for The Bible as Literature.
    """

    barcode = "HNU1G9"
    title = "The Bible as Literature: an introduction"
    author = "Wood, Irving Francis"
    date = "1914"

    notes = """
    Literary analysis of the Bible.

    Known quirks:
    - Discussion of biblical genres (proverbs, etc.)
    - Verse references (16. 1-9, 14)
    - Analysis of Hebrew literature structure
    - References to Jehovah, the king
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
        """Book-specific cleanup for The Bible as Literature."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
