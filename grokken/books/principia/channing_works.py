"""
Handler for "The Works of William E. Channing, D.D." (1875).

Collected works of William Ellery Channing, the prominent Unitarian minister
and theologian. One of the largest books in the Principia 34 at over 1M tokens.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class ChanningWorks(BookProcessor):
    """
    Processor for The Works of William E. Channing.
    """

    barcode = "AH3KTH"
    title = "The Works of William E. Channing, D.D."
    author = "Channing, William Ellery"
    date = "1875"

    notes = """
    Collected theological and philosophical works of William Ellery Channing.

    Known quirks:
    - Very large (1M+ tokens)
    - Theological/philosophical essays
    - Discussion of Calvinism, Unitarianism
    - Multiple essays/sermons collected together
    - Running headers with essay titles
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
        """Book-specific cleanup for Works of William E. Channing."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
