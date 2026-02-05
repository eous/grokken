"""
Handler for "The Elements of International Law" by George B. Davis (1903 edition).

An alternate edition of Davis's legal textbook, with an account of its origin.

Score: 37.8
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class InternationalLawDavis1903(BookProcessor):
    """
    Processor for The Elements of International Law (1903).
    """

    barcode = "HWQTYU"
    title = "The Elements of International Law; with an account of its origin"
    author = "Davis, George B."
    date = "1903"

    notes = """
    Later edition of Davis's international law textbook.

    Known quirks:
    - Extensive footnotes with legal citations
    - References to Pradier-Fodéré, Halleck, Phillimore, etc.
    - Legal terminology and case references
    - Running headers possible
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
        """Book-specific cleanup for Elements of International Law (1903)."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
