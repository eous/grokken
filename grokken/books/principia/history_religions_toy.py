"""
Handler for "Introduction to the History of Religions" by Crawford Howell Toy (1913).

A scholarly introduction to comparative religion, part of the Handbooks on
the History of Religions series edited by Morris Jastrow Jr.

Score: 38.8
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class HistoryOfReligions(BookProcessor):
    """
    Processor for Introduction to the History of Religions.
    """

    barcode = "TZ1WHG"
    title = "Introduction to the History of Religions"
    author = "Toy, Crawford Howell"
    date = "1913"

    notes = """
    Academic text on comparative religion.

    Known quirks:
    - Library stamps at beginning (Tozzer Library, Peabody Museum)
    - Extensive footnotes with superscript numbers
    - Running headers "INTRODUCTION TO HISTORY OF RELIGIONS"
    - References to other works (Records of the Past, etc.)
    - Section numbers (e.g., "728.")
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
        """Book-specific cleanup for Introduction to History of Religions."""
        import regex as re

        # Remove running headers with page numbers
        text = re.sub(
            r"^\s*\d+\s+INTRODUCTION TO HISTORY OF RELIGIONS\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*INTRODUCTION TO HISTORY OF RELIGIONS\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
