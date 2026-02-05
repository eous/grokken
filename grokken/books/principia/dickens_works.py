"""
Handler for "The Works of Charles Dickens" (1911 Anniversary Edition).

Part of a collected works edition with introductions by Andrew Lang,
Frederic G. Kitton, John Forster, G. K. Chesterton, George Gissing, and others.

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class DickensWorks(BookProcessor):
    """
    Processor for The Works of Charles Dickens.
    """

    barcode = "HWABNK"
    title = "The Works of Charles Dickens"
    author = "Dickens, Charles"
    date = "1911"

    notes = """
    Anniversary Edition of Dickens's collected works, specifically Pickwick Papers Part I.

    Known quirks:
    - Heavy OCR noise from illustrated plates and decorative elements
    - Library stamps (Harvard College Library, Widener)
    - Multiple introductions by various critics
    - Dialogue-heavy prose
    - Chapter/Part markers
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
        """Book-specific cleanup for Works of Charles Dickens."""
        import regex as re

        # Remove running headers like "PICKWICK PAPERS" with page numbers
        text = re.sub(
            r"^\s*\d+\s+PICKWICK PAPERS\.?\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*PICKWICK PAPERS\.?\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        # Clean up OCR artifacts from illustrations (sequences of single chars)
        text = re.sub(r"^[A-Z]\s*$\n", "", text, flags=re.MULTILINE)

        return text
