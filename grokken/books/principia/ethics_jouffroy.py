"""
Handler for "Introduction to Ethics" by Theodore Jouffroy (1840).

A philosophical work including a critical survey of moral systems.
Translated from French.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class IntroductionToEthics(BookProcessor):
    """
    Processor for Introduction to Ethics.
    """

    barcode = "AH3HJZ"
    title = "Introduction to Ethics: including a critical survey of moral systems"
    author = "Jouffroy, Theodore"
    date = "1840"

    notes = """
    French philosophical work on ethics, translated to English.

    Known quirks:
    - Philosophical/metaphysical content
    - Discussion of various moral systems
    - Dense prose style typical of 19th century philosophy
    - References to Spinoza, other philosophers
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1840 text
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Introduction to Ethics."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
