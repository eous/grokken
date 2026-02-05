"""
Handler for "Evolution of To-day" by H. W. Conn (1886).

A summary of the theory of evolution as held by scientists of the present day.

Score: 36.0
"""

from grokken.base import BookProcessor
from grokken.transforms import encoding, ocr, typography, whitespace


class EvolutionToday(BookProcessor):
    """
    Processor for Evolution of To-day.
    """

    barcode = "HN28C4"
    title = "Evolution of To-day: a summary of the theory of evolution"
    author = "Conn, H. W."
    date = "1886"

    notes = """
    Scientific summary of evolutionary theory.

    Known quirks:
    - Scientific terminology (fossils, species, genera)
    - Discussion of geographical distribution
    - References to migrations, localities
    - Late 19th century scientific prose
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
        """Book-specific cleanup for Evolution of To-day."""
        import regex as re

        # Remove standalone page numbers
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        return text
