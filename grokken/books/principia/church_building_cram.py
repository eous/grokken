"""
Handler for "Church Building" by Ralph Adams Cram (1901).

A study of the principles of architecture in their relation to the church.
The smallest category (Fine Arts) representative.

Score: 37.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class ChurchBuilding(BookProcessor):
    """
    Processor for Church Building.
    """

    barcode = "32044038386975"
    title = "Church Building: a study of the principles of architecture"
    author = "Cram, Ralph Adams"
    date = "1901"

    notes = """
    Architectural study of church design.

    Known quirks:
    - Figure/plate references (J. D. Sedding, Architect, etc.)
    - Architectural terminology (credence, sedilia, stalls)
    - Roman numeral figure numbers (LXI)
    - Descriptions of church elements
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
        """Book-specific cleanup for Church Building."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
