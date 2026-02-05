"""
Handler for "Manual of Parliamentary Practice" by Luther Stearns Cushing (1877).

A procedural manual on rules of proceeding and debate in deliberative assemblies.
The smallest book in the Principia 34 at ~52k tokens.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class ParliamentaryPractice(BookProcessor):
    """
    Processor for Manual of Parliamentary Practice.
    """

    barcode = "HN6KER"
    title = "Manual of Parliamentary Practice: rules of proceeding and debate"
    author = "Cushing, Luther Stearns"
    date = "1877"

    notes = """
    Procedural manual for parliamentary proceedings.

    Known quirks:
    - Numbered sections and rules
    - Legal/procedural language
    - Cross-references between sections
    - Smallest book in collection (~52k tokens)
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
        """Book-specific cleanup for Manual of Parliamentary Practice."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
