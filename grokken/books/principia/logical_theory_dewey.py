"""
Handler for "Studies in Logical Theory" by John Dewey (1903).

A philosophical work on logic and epistemology.

Score: 37.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class LogicalTheory(BookProcessor):
    """
    Processor for Studies in Logical Theory.
    """

    barcode = "32044069804946"
    title = "Studies in Logical Theory"
    author = "Dewey, John"
    date = "1903"

    notes = """
    Dewey's philosophical work on logic.

    Known quirks:
    - Philosophical/epistemological content
    - Discussion of meaning, ideas, images
    - Running headers "STUDIES IN LOGICAL THEORY"
    - Academic prose style
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
        """Book-specific cleanup for Studies in Logical Theory."""
        import regex as re

        # Remove running headers
        text = re.sub(
            r"^\s*\d+\s+STUDIES IN LOGICAL THEORY\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*STUDIES IN LOGICAL THEORY\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
