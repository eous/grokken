"""
Handler for "A Text-book of the Principles of Animal Histology" by Ulric Dahlgren (1908).

A scientific textbook on animal histology (microscopic anatomy of animal tissues).

Score: 38.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class AnimalHistology(BookProcessor):
    """
    Processor for A Text-book of the Principles of Animal Histology.
    """

    barcode = "HN2WWN"
    title = "A Text-book of the Principles of Animal Histology"
    author = "Dahlgren, Ulric"
    date = "1908"

    notes = """
    Scientific textbook on animal histology.

    Known quirks:
    - Many figure references and diagram descriptions
    - Running headers "HISTOLOGY"
    - Technical terminology (rods, cones, cells, etc.)
    - References to other texts (Stohr's Text-book, Lewis)
    - Abbreviations in figure legends (bl.v., pg., etc.)
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
        """Book-specific cleanup for Principles of Animal Histology."""
        import regex as re

        # Remove running headers with page numbers
        text = re.sub(
            r"^\s*\d+\s+HISTOLOGY\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\s*HISTOLOGY\s+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
