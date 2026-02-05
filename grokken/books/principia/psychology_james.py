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
    author = "James, William"
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

        1. Removes front matter (library stamps, title page, table of contents)
        2. Removes back matter (index, advertisements, library stamps)
        3. Removes running headers throughout the book
        """
        import regex as re

        # === STRIP FRONT MATTER ===
        # Front matter includes: library stamps, title page, copyright, table of contents
        # Actual content starts with "PSYCHOLOGY.\nCHAPTER XVII."
        front_marker = "PSYCHOLOGY.\nCHAPTER XVII."
        front_pos = text.find(front_marker)
        if front_pos > 0:
            # Keep from "CHAPTER XVII." onwards
            text = text[front_pos + len("PSYCHOLOGY.\n"):]

        # === STRIP BACK MATTER ===
        # Book ends with "THE END." followed by index, ads, library stamps
        end_match = re.search(r"THE END\.\s*\n", text)
        if end_match:
            text = text[:end_match.end()]

        # === REMOVE RUNNING HEADERS ===

        # Pattern 1: Page number on own line, followed by "PSYCHOLOGY." (or OCR variants)
        # Matches: "\n322\nPSYCHOLOGY.\n" or "\n322\nPSYCHOLOG Y.\n" (OCR error with space)
        text = re.sub(
            r"\n\d{1,4}\nPSYCHOLOG\s?Y\.\n",
            "\n",
            text,
        )

        # Pattern 2: Page number on own line, followed by other all-caps headers
        # (chapter titles like "SENSATION.", "IMAGINATION.", "INDEX.", etc.)
        # Note: Use [ ] (space only) not [\s] to avoid matching newlines
        text = re.sub(
            r"\n\d{1,4}\n([A-Z][A-Z ]{2,50}\.)\n",
            "\n",
            text,
        )

        # Pattern 3: All-caps header on own line, followed by page number on next line
        # Matches: "SENSATION.\n3\n" or "NECESSARY TRUTHS-EFFECTS OF EXPERIENCE.\n689\n"
        # Note: Use [ -] (space and hyphen) not [\s-] to avoid matching newlines
        text = re.sub(
            r"\n([A-Z][A-Z -]{2,50}\.)\n\d{1,4}\n",
            "\n",
            text,
        )

        # Pattern 4: Page number followed by header on same line (original patterns)
        # Note: Use [ ] (space only) not [\s] to avoid matching newlines
        text = re.sub(
            r"^[ \t]*\d+[ \t]+(PRINCIPLES OF PSYCHOLOGY|[A-Z][A-Z ]+)[ \t]*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Pattern 5: Chapter title followed by page number on same line
        # Includes hyphens for titles like "NECESSARY TRUTHS-EFFECTS OF EXPERIENCE."
        # Note: Use [ -] (space and hyphen) not [\s-] to avoid matching newlines
        text = re.sub(
            r"^([A-Z][A-Z -]+\.?)[ \t]+\d+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # Clean up any resulting multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # === REFLOW PARAGRAPHS ===
        # Join lines that are mid-paragraph (OCR line breaks within sentences)
        # Pattern: lowercase letter at end of line, newline, lowercase letter at start
        # Replace with: lowercase, space, lowercase (joining the lines)
        text = re.sub(r"([a-z,;:])\n([a-z])", r"\1 \2", text)

        # Also handle cases ending with closing quote or parenthesis
        text = re.sub(r"([a-z]['\")])\n([a-z])", r"\1 \2", text)

        return text
