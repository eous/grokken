"""
Handler for "The Doctrines of Friends, or, Principles of the Christian Religion"
by Elisha Bates (1825).

A work on Quaker theology and principles. The oldest book in the Principia 34.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class DoctrinesOfFriends(BookProcessor):
    """
    Processor for The Doctrines of Friends.
    """

    barcode = "HWJN82"
    title = "The Doctrines of Friends, or, Principles of the Christian Religion"
    author = "Bates, Elisha"
    date = "1825"

    notes = """
    Quaker theological work, oldest book in the collection (1825).

    Known quirks:
    - Older typography and spelling conventions
    - Religious/theological content
    - Biblical references and quotations
    - May have more OCR issues due to age of source material
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1825 text
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Doctrines of Friends."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
