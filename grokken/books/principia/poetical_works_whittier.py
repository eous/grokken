"""
Handler for "The Complete Poetical Works of John Greenleaf Whittier" (1873).

Collected poetry of the American Quaker poet and abolitionist.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class WhittierPoetry(BookProcessor):
    """
    Processor for The Complete Poetical Works of John Greenleaf Whittier.
    """

    barcode = "HWK6N4"
    title = "The Complete Poetical Works of John Greenleaf Whittier"
    author = "Whittier, John Greenleaf"
    date = "1873"

    notes = """
    Collected poetry of John Greenleaf Whittier.

    Known quirks:
    - Poetry formatting (line breaks matter)
    - Rhyme schemes and meter
    - Various poem lengths and styles
    - May need careful handling of line breaks
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
        # Note: NOT using dehyphenate aggressively for poetry
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Whittier's Poetical Works."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
