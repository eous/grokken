"""
Handler for William James's "The Principles of Psychology" (1890).

This is the top-scoring book in The Principia 34 (score: 39.0).
A foundational work in psychology, known for its comprehensive
treatment of consciousness, habit, emotion, and the self.

Two volumes, ~400K tokens.
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class PrinciplesPsychology(BookProcessor):
    """
    Processor for William James's Principles of Psychology.
    """

    barcode = "32044010149714"
    title = "The Principles of Psychology"
    author = "William James"
    date = "1890"

    notes = """
    Two-volume work, considered foundational in psychology.

    Known quirks:
    - Headers alternate between chapter title and "PRINCIPLES OF PSYCHOLOGY"
    - Footnotes use superscript numbers
    - Contains occasional Greek passages (untransliterated)
    - Some figures/diagrams referenced but not present in OCR

    The OCR quality is generally good (high OCR score contributed to
    its top ranking).
    """

    transforms = [
        # Encoding cleanup
        encoding.normalize_to_utf8,
        encoding.normalize_line_endings,

        # Typography
        typography.fix_ligatures,
        typography.normalize_quotes,
        typography.normalize_dashes,
        typography.normalize_spaces,

        # OCR fixes
        ocr.fix_common_errors,
        ocr.fix_digit_letter_confusion,
        ocr.remove_ocr_artifacts,

        # Whitespace
        whitespace.dehyphenate,
        whitespace.normalize_whitespace,
        whitespace.collapse_blank_lines(max_consecutive=2),
        whitespace.trim,
    ]

    def post_process(self, text: str) -> str:
        """
        Book-specific cleanup for Principles of Psychology.
        """
        # Remove running headers (common pattern in this book)
        import regex as re

        # Pattern: page number followed by chapter title or book title
        text = re.sub(
            r"^\s*\d+\s+(PRINCIPLES OF PSYCHOLOGY|[A-Z][A-Z\s]+)\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Pattern: chapter title followed by page number
        text = re.sub(
            r"^([A-Z][A-Z\s]+)\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        return text
