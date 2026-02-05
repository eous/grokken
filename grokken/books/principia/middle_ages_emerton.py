"""
Handler for "An Introduction to the Study of the Middle Ages (375-814)"
by Ephraim Emerton (1888).

A historical text covering early medieval history.

Score: 36.8
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class MiddleAges(BookProcessor):
    """
    Processor for Introduction to the Study of the Middle Ages.
    """

    barcode = "HWQXIB"
    title = "An Introduction to the Study of the Middle Ages (375-814)"
    author = "Emerton, Ephraim"
    date = "1888"

    notes = """
    Historical introduction to early medieval period.

    Known quirks:
    - Historical narrative covering 375-814 CE
    - Discussion of Bavaria, nobility, organization
    - Place names and historical figures
    - Academic historical prose
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
        """Book-specific cleanup for Introduction to the Middle Ages."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
