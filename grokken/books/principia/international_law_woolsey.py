"""
Handler for "Introduction to the Study of International Law" by Theodore Dwight Woolsey (1879).

A textbook designed as an aid in teaching and in historical studies.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class InternationalLawWoolsey(BookProcessor):
    """
    Processor for Introduction to the Study of International Law.
    """

    barcode = "32044103157517"
    title = "Introduction to the Study of International Law"
    author = "Woolsey, Theodore Dwight"
    date = "1879"

    notes = """
    Educational text on international law.

    Known quirks:
    - Designed for teaching/study
    - Discussion of neutrality, war, treaties
    - Legal principles and historical examples
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
        """Book-specific cleanup for Introduction to International Law."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
