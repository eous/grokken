"""
Handler for "The Principles of Sociology" by Herbert Spencer (1895).

Spencer's foundational work applying evolutionary principles to social organization.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class SociologySpencer(BookProcessor):
    """
    Processor for The Principles of Sociology.
    """

    barcode = "32044020258091"
    title = "The Principles of Sociology"
    author = "Spencer, Herbert"
    date = "1895"

    notes = """
    Spencer's evolutionary sociology work.

    Known quirks:
    - Scientific/philosophical prose
    - Discussion of biological and social evolution
    - Technical terminology
    - Running headers likely present
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
        """Book-specific cleanup for Principles of Sociology."""
        import regex as re

        # Remove running headers
        text = re.sub(
            r"^\s*\d+\s+PRINCIPLES OF SOCIOLOGY\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*PRINCIPLES OF SOCIOLOGY\.?\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
