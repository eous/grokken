"""
Handler for "The Principles of Pathologic Histology" by Frank B. Mallory (1914).

A medical textbook with 497 figures containing 683 illustrations, 124 in colors.
Published by W. B. Saunders Company.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class PathologicHistology(BookProcessor):
    """
    Processor for The Principles of Pathologic Histology.
    """

    barcode = "HC1BZF"
    title = "The Principles of Pathologic Histology"
    author = "Mallory, Frank Burr"
    date = "1914"

    notes = """
    Medical textbook on pathologic histology.

    Known quirks:
    - Many figure references (Fig. 257, etc.)
    - Running headers "PATHOLOGIC HISTOLOGY"
    - Technical/medical terminology
    - Descriptions of microscopic observations
    - Library stamps (Countway Library)
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
        """Book-specific cleanup for Principles of Pathologic Histology."""
        import regex as re

        # Remove running headers with page numbers
        text = re.sub(
            r"^\s*\d+\s+PATHOLOGIC HISTOLOGY\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*PATHOLOGIC HISTOLOGY\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
