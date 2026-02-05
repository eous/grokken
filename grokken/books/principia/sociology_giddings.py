"""
Handler for "The Elements of Sociology" by Franklin Henry Giddings (1898).

A text-book for colleges and schools on sociological principles.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class SociologyGiddings(BookProcessor):
    """
    Processor for The Elements of Sociology.
    """

    barcode = "TZ1HCP"
    title = "The Elements of Sociology: a text-book for colleges and schools"
    author = "Giddings, Franklin Henry"
    date = "1898"

    notes = """
    Sociology textbook for educational use.

    Known quirks:
    - Academic sociology content
    - Discussion of family structures, tribes
    - References to Greenland, Brazil, various cultures
    - Sociological terminology (polyandrian, savagery)
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
        """Book-specific cleanup for The Elements of Sociology."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
