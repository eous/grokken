"""
Handler for "The Atonement: discourses and treatises" (1859).

A collection of theological discourses by Edwards, Smalley, Maxcy, Emmons,
Griffin, Burge, and Weeks, with an introductory essay by Edwards A. Park.

Score: 39.0 (tied for highest in Principia 34)
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class Atonement(BookProcessor):
    """
    Processor for The Atonement: discourses and treatises.
    """

    barcode = "HWT5II"
    title = "The Atonement: discourses and treatises"
    author = "Edwards, Smalley, Maxcy, Emmons, Griffin, Burge, Weeks"
    date = "1859"

    notes = """
    Collection of theological discourses on the atonement doctrine.

    Known quirks:
    - Heavy front matter with library stamps, catalog numbers
    - Multiple authors/sections
    - Biblical quotations throughout
    - Footnotes with references
    - Running headers "THE ATONEMENT" or discourse titles
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
        """Book-specific cleanup for The Atonement."""
        import regex as re

        # Remove running headers with page numbers
        text = re.sub(
            r"^\s*\d+\s+THE ATONEMENT\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*THE ATONEMENT\.?\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
