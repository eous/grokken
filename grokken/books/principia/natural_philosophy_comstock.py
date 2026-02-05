"""
Handler for "A System of Natural Philosophy" by J. L. Comstock (1835).

A natural philosophy (physics) textbook from the early 19th century.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class NaturalPhilosophy(BookProcessor):
    """
    Processor for A System of Natural Philosophy.
    """

    barcode = "32044097047575"
    title = "A System of Natural Philosophy"
    author = "Comstock, J. L."
    date = "1835"

    notes = """
    Early natural philosophy/physics textbook.

    Known quirks:
    - Q&A format (questions and answers)
    - Discussion of light, optics, colors
    - Older scientific terminology
    - May have more OCR issues due to age (1835)
    """

    transforms = [
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,
        ocr.fix_common_errors,
        ocr.fix_long_s,  # Important for 1835 text
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """Book-specific cleanup for A System of Natural Philosophy."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
