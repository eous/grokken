"""
Handler for "The Writings of Harriet Beecher Stowe" (1896 Riverside Edition).

Volume XIII of a sixteen-volume collection with biographical introductions,
portraits, and other illustrations.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class StoweWritings(BookProcessor):
    """
    Processor for The Writings of Harriet Beecher Stowe.
    """

    barcode = "32044094451689"
    title = "The Writings of Harriet Beecher Stowe"
    author = "Stowe, Harriet Beecher"
    date = "1896"

    notes = """
    Riverside Edition, Volume XIII of collected works.

    Known quirks:
    - Library stamps (Child Memorial Library, Harvard)
    - Multi-volume reference markers
    - Clean prose in main text
    - Some moral/philosophical essays
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
        """Book-specific cleanup for Writings of Harriet Beecher Stowe."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
