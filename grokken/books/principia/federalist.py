"""
Handler for "The Federalist" (1864 reprint).

A collection of essays written in favor of the new Constitution by
Alexander Hamilton, James Madison, and John Jay.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class Federalist(BookProcessor):
    """
    Processor for The Federalist.
    """

    barcode = "32044072043805"
    title = "The Federalist: a collection of essays in favor of the new Constitution"
    author = "Hamilton, Madison, Jay"
    date = "1864"

    notes = """
    The Federalist Papers - foundational American political philosophy.

    Known quirks:
    - Political philosophy and constitutional argument
    - Running headers "The Federalist."
    - Discussion of Confederation, Convention
    - Formal 18th century prose style
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
        """Book-specific cleanup for The Federalist."""
        import regex as re

        # Remove running headers
        text = re.sub(
            r"^\s*\d+\s+The Federalist\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*The Federalist\.?\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
