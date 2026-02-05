"""
Handler for "The Vicarious Sacrifice" by Horace Bushnell (1866).

A theological work grounded in principles of universal obligation.

Score: 37.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class VicariousSacrifice(BookProcessor):
    """
    Processor for The Vicarious Sacrifice.
    """

    barcode = "32044018647321"
    title = "The Vicarious Sacrifice, grounded in principles of universal obligation"
    author = "Bushnell, Horace"
    date = "1866"

    notes = """
    Theological treatise on atonement and sacrifice.

    Known quirks:
    - Religious/theological content
    - Biblical quotations and references
    - Dense theological prose
    - Phrases like "the wrath of the Lamb"
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
        """Book-specific cleanup for The Vicarious Sacrifice."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
