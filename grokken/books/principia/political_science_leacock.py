"""
Handler for "Elements of Political Science" by Stephen Leacock (1906).

A textbook on political science covering government structures, constitutional law,
and comparative politics.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class PoliticalScience(BookProcessor):
    """
    Processor for Elements of Political Science.
    """

    barcode = "32044097049340"
    title = "Elements of Political Science"
    author = "Leacock, Stephen"
    date = "1906"

    notes = """
    Political science textbook by Stephen Leacock (also known as a humorist).

    Known quirks:
    - Many numbered lists (ministers, departments)
    - Comparative government structure tables
    - Chapter/section organization
    - Clean academic prose
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
        """Book-specific cleanup for Elements of Political Science."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
