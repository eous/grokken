"""
Handler for "The Elements of International Law" by George B. Davis (1900).

A legal textbook on international law principles.

Score: 37.9
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class InternationalLawDavis1900(BookProcessor):
    """
    Processor for The Elements of International Law (1900).
    """

    barcode = "32044103157418"
    title = "The Elements of International Law"
    author = "Davis, George B."
    date = "1900"

    notes = """
    Legal textbook on international law.

    Known quirks:
    - Legal citations and references
    - Footnotes with case references
    - Discussion of war, treaties, neutrality
    - Formal legal prose
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
        """Book-specific cleanup for Elements of International Law."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
