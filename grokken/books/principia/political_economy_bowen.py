"""
Handler for "The Principles of Political Economy" by Francis Bowen (1856).

Applied to the condition, resources, and institutions of the American people.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class PoliticalEconomyBowen(BookProcessor):
    """
    Processor for The Principles of Political Economy (Bowen).
    """

    barcode = "32044018740308"
    title = "The Principles of Political Economy applied to the American people"
    author = "Bowen, Francis"
    date = "1856"

    notes = """
    American political economy focused on US conditions.

    Known quirks:
    - Discussion of agriculture, labor, production
    - American economic context
    - Statistical and economic terminology
    - References to civilized countries, inhabitants
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
        """Book-specific cleanup for Principles of Political Economy (Bowen)."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
