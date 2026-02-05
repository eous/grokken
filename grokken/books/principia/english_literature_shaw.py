"""
Handler for "A Complete Manual of English Literature" by Thomas B. Shaw (1867).

A comprehensive guide to English literature.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class EnglishLiterature(BookProcessor):
    """
    Processor for A Complete Manual of English Literature.
    """

    barcode = "HWPLDT"
    title = "A Complete Manual of English Literature"
    author = "Shaw, Thomas B."
    date = "1867"

    notes = """
    Literary criticism and history of English literature.

    Known quirks:
    - Discussion of various literary works and authors
    - Literary analysis and criticism
    - References to classical and English literature
    - May contain poetry quotations
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
        whitespace.dehyphenate,  # Kept for prose criticism; poetry quotes are brief
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for Manual of English Literature."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
