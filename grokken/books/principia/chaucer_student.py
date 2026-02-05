"""
Handler for "The Student's Chaucer" (1895).

A complete edition of Geoffrey Chaucer's works. The largest book in the
Principia 34 at over 1M tokens.

Score: 37.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class StudentChaucer(BookProcessor):
    """
    Processor for The Student's Chaucer.
    """

    barcode = "HWKBVP"
    title = "The Student's Chaucer, being a complete edition of his works"
    author = "Chaucer, Geoffrey"
    date = "1895"

    notes = """
    Complete works of Geoffrey Chaucer. Largest book in the collection.

    Known quirks:
    - Middle English text
    - Latin phrases (Explicit tercia pars, Sequitur pars quarta)
    - Poetry formatting with line numbers
    - Very large (1M+ tokens)
    - Archaic spelling throughout
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for older text
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,
        # Note: careful with dehyphenation due to poetry
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for The Student's Chaucer."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
