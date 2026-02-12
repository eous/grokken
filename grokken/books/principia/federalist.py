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
        ocr.fix_long_s,  # 1864 reprint of 1788 text
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
        Book-specific cleanup for The Federalist.

        1. Strips front matter (library stamps, title page, copyright, advertisement, TOC)
        2. Strips back matter (library stamps after "END OF VOL. I.")
        3. Fixes book-specific OCR errors (Jáy, œ ligatures, garbage chars)
        4. Removes running headers in all variant forms
        5. Removes VOL. I. section markers and standalone page numbers
        6. Reflows paragraphs broken by OCR line breaks
        """
        import regex as re

        # === STRIP FRONT MATTER ===
        # Content starts with "INTRODUCTION." (the section header for the editor's
        # introduction by Henry B. Dawson). Everything before is library stamps,
        # title page, copyright, dedication, Advertisement, and Table of Contents.
        front_match = re.search(r"^INTRODUCTION\.\s*$", text, re.MULTILINE)
        if front_match:
            text = text[front_match.start() :]

        # === STRIP BACK MATTER ===
        # Book ends with "END OF VOL. I." followed by library stamps/garbage
        end_match = re.search(r"END OF VOL\.\s*I\.\s*\n", text)
        if end_match:
            text = text[: end_match.end()]

        # === BOOK-SPECIFIC OCR FIXES ===

        # "Jáy" is a consistent OCR misread of "Jay"
        text = text.replace("Jáy", "Jay")

        # Expand œ/Œ ligatures per typography.py guidance for book-specific post_process.
        # Case-aware: Œ before uppercase → OE (FŒDERAL → FOEDERAL),
        # otherwise Œ → Oe, œ → oe
        text = re.sub(r"\u0152(?=[A-Z])", "OE", text)
        text = text.replace("\u0152", "Oe").replace("\u0153", "oe")

        # Normalize ornamental quote marks to ASCII
        text = text.replace("\u275d", '"').replace("\u275e", '"')

        # Fix Cyrillic/Greek homoglyphs (OCR confuses visually similar scripts)
        text = text.replace("\u03a4\u039f", "TO")  # Greek ΤΟ → TO
        text = text.replace("\u03a4\u03bf", "To")  # Greek Το → To
        text = text.replace("\u0410", "A")  # Cyrillic А → A (ACHEUS)
        # Cyrillic м → m; then fix mangled proper names where it should be M
        text = text.replace("\u043c", "m")
        text = text.replace("RomULUS", "ROMULUS")
        text = re.sub(r"THOm-?\n?AS\b", "THOMAS", text)

        # Remove non-Latin script OCR garbage (Tibetan, Arabic, Korean, Thai, CJK,
        # and remaining Greek/Cyrillic chars that aren't Latin homoglyphs)
        text = re.sub(
            r"[\u0370-\u03ff\u0400-\u04ff\u0600-\u06ff\u0e00-\u0e7f"
            r"\u0f00-\u0fff\u4e00-\u9fff\uac00-\ud7af\u3130-\u318f]",
            "",
            text,
        )

        # Fix dot-below OCR artifact: ị → i (in "whịch" etc.)
        text = text.replace("\u1ecb", "i")

        # Fix superscript digits (OCR artifacts from split capitals at page boundaries).
        # Rejoin drop-cap splits: A¹\nFTER → AFTER. Requires the capital to be at
        # line start and the continuation to be 2+ uppercase chars (avoids joining
        # a footnote superscript at end of a word with a new line).
        text = re.sub(
            r"(?<=\n)([A-Z])[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]+\n([A-Z]{2,})",
            r"\1\2",
            text,
        )
        # Then remove any remaining superscript digits (footnote markers etc.)
        text = re.sub(r"[\u2070\u00b9\u00b2\u00b3\u2074-\u2079]", "", text)

        # Remove bullet and symbol OCR artifacts
        text = re.sub(r"[\u2022\u26ab\u25bc\u00bf]", "", text)  # •⚫▼¿
        text = text.replace("\u2758", "|")  # ❘ → |
        text = text.replace("\u00b7", ".")  # · → .

        # Normalize ellipsis runs (dot leaders in TOC sections)
        text = re.sub(r"\u2026+", "...", text)
        text = re.sub(r"\.{4,}", "...", text)

        # === REMOVE RUNNING HEADERS ===
        # Headers appear as "The F[oe]deralist." / "Introduction." / "Contents." /
        # "Advertisement." in 4 positional forms, plus all-caps "THE FEDERALIST."

        header = r"(The\s+F[oe]{0,2}deralist|Introduction|Contents|Advertisement)\."

        # Pattern A: Page number on own line, then header on next line
        # Allow optional leading +/* from OCR errors (e.g. "+3" for "43")
        text = re.sub(rf"\n[+*]?\d{{1,4}}\n{header}\n", "\n", text)

        # Pattern B: Header on own line, then page number on next line
        text = re.sub(rf"\n{header}\n\d{{1,4}}\n", "\n", text)

        # Pattern C: Page number + header on same line
        text = re.sub(rf"^\s*\d+\s+{header}\s*$", "", text, flags=re.MULTILINE)

        # Pattern D: Header + page number on same line
        text = re.sub(rf"^\s*{header}\s+\d+\s*$", "", text, flags=re.MULTILINE)

        # All-caps "THE FEDERALIST." running headers (not essay headers which
        # include "No. X", so those are preserved)
        text = re.sub(r"^\s*THE\s+FEDERALIST\.?\s*$", "", text, flags=re.MULTILINE)

        # Standalone running header lines (no adjacent page number).
        # Title-case only — the all-caps "INTRODUCTION." section header is preserved.
        text = re.sub(
            r"^\s*(Introduction|Contents|Advertisement)\.\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # === REMOVE VOL. I. SECTION MARKERS ===
        # These appear mid-text as "VOL. I.\n{page_id}\n" where page_id may be a
        # digit, a letter (b, c, d, e, g, h in the introduction), or absent.
        # Negative lookbehind preserves "END OF VOL. I."
        text = re.sub(r"(?<!END OF )VOL\.\s*I\.\s*\n", "\n", text)

        # === REMOVE STANDALONE PAGE NUMBERS ===
        text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

        # === REMOVE LETTER PAGE IDENTIFIERS ===
        # The introduction uses single-letter page IDs (b, c, d, e, g, h)
        text = re.sub(r"^\s*[a-h]\s*$", "", text, flags=re.MULTILINE)

        # === REMOVE ROMAN NUMERAL PAGE NUMBERS ===
        # The introduction uses roman numerals (ii, iii, iv, etc.).
        # Require 2+ chars to avoid matching the pronoun "I" or single letters.
        # Case-consistent to avoid matching words like "ill" or "Civil".
        text = re.sub(r"^\s*(?:[ivxlc]{2,6}|[IVXLC]{2,6})\s*$", "", text, flags=re.MULTILINE)

        # === CLEAN UP MULTIPLE BLANK LINES ===
        text = re.sub(r"\n{3,}", "\n\n", text)

        # === DEHYPHENATE ACROSS PAGE BOUNDARIES ===
        # The standard dehyphenate runs before post_process, so it can't catch
        # hyphens split across page boundaries (headers were still present).
        # After header removal + blank line collapse, these appear as word-\n\nword.
        # Tradeoff: could false-join a compound word at end of paragraph with the
        # next paragraph, but this is rare — paragraph-final hyphens in 18th-century
        # prose are almost always line-break artifacts, not compound words.
        text = re.sub(r"(\w)-\n\n([a-z])", r"\1\2", text)
        # Also catch hyphens with trailing spaces (left after symbol removal,
        # e.g. "considera- •\ntions" → "considera- \ntions" → "considerations")
        text = re.sub(r"(\w)- +\n([a-z])", r"\1\2", text)

        # === REFLOW PARAGRAPHS ===
        # Join lines that are mid-paragraph (OCR line breaks within sentences)
        text = re.sub(r"([a-z,;:])\n([a-z])", r"\1 \2", text)
        # Period followed by lowercase = mid-sentence break, not a paragraph boundary
        text = re.sub(r"([a-z]\.)\n([a-z])", r"\1 \2", text)
        # Also handle cases ending with closing quote or parenthesis
        text = re.sub(r"([a-z]['\")])\n([a-z])", r"\1 \2", text)

        return text
