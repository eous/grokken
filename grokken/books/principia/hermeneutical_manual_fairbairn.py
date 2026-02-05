"""
Handler for "Hermeneutical Manual" by Patrick Fairbairn (1859).

An introduction to the exegetical study of the Scriptures.

Score: 37.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class HermeneuticalManual(BookProcessor):
    """
    Processor for Hermeneutical Manual.
    """

    barcode = "HNVJ7R"
    title = "Hermeneutical Manual: Introduction to the exegetical study of Scripture"
    author = "Fairbairn, Patrick"
    date = "1859"

    notes = """
    Biblical hermeneutics/interpretation manual.

    Known quirks:
    - Biblical references and Greek/Hebrew terms
    - Discussion of Jesus, resurrection, Scripture
    - Theological terminology
    - References to followers, disciples
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
        """Book-specific cleanup for Hermeneutical Manual."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
