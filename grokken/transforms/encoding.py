"""
Encoding-related transforms.

Handles character encoding issues common in OCR'd historical texts.
"""

import regex as re

# Replacement pairs for normalize_to_utf8 (order matters for multi-char mojibake)
_UTF8_REPLACEMENTS = [
    # Windows-1252 artifacts that appear as UTF-8
    ("\x92", "'"),  # Right single quote
    ("\x93", '"'),  # Left double quote
    ("\x94", '"'),  # Right double quote
    ("\x96", "\u2013"),  # En dash
    ("\x97", "\u2014"),  # Em dash
    # Latin-1 artifacts
    ("\xa0", " "),  # Non-breaking space
    ("\xad", ""),  # Soft hyphen
    # Common mojibake patterns (UTF-8 misinterpreted as CP1252)
    ("\u00e2\u20ac\u2122", "'"),  # Right single quote mojibake
    ("\u00e2\u20ac\u0153", '"'),  # Left double quote mojibake
    ("\u00e2\u20ac\x9d", '"'),  # Right double quote mojibake
    ("\u00e2\u20ac\u201d", "\u2014"),  # Em dash mojibake
    ("\u00e2\u20ac\u201c", "\u2013"),  # En dash mojibake
    ("\u00c3\u00a9", "\u00e9"),  # e-acute mojibake
    ("\u00c3\u00a8", "\u00e8"),  # e-grave mojibake
    ("\u00c3\u00a2", "\u00e2"),  # a-circumflex mojibake
    ("\u00c3\u00b4", "\u00f4"),  # o-circumflex mojibake
    ("\u00c3\u00ae", "\u00ee"),  # i-circumflex mojibake
    ("\u00c3\u00bb", "\u00fb"),  # u-circumflex mojibake
    ("\u00c3\u00a7", "\u00e7"),  # c-cedilla mojibake
]

# Precompiled pattern for fix_unicode_escapes
_RE_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def normalize_to_utf8(text: str) -> str:
    """
    Normalize text to clean UTF-8.

    Replaces common encoding artifacts with correct characters.
    """
    for old, new in _UTF8_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def strip_null_bytes(text: str) -> str:
    """Remove null bytes that sometimes appear in OCR output."""
    return text.replace("\x00", "")


def normalize_line_endings(text: str) -> str:
    """Normalize all line endings to Unix-style (LF)."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def fix_unicode_escapes(text: str) -> str:
    """
    Fix incorrectly escaped Unicode sequences.

    Sometimes OCR produces literal \\u0041 instead of A.
    """

    def replace_escape(match):
        try:
            codepoint = int(match.group(1), 16)
            # Skip control characters and bidi overrides
            if codepoint < 0x20 or 0x7F <= codepoint <= 0x9F:
                return match.group(0)
            if 0x200B <= codepoint <= 0x200F or 0x202A <= codepoint <= 0x202E:
                return match.group(0)
            return chr(codepoint)
        except (ValueError, OverflowError):
            return match.group(0)

    return _RE_UNICODE_ESCAPE.sub(replace_escape, text)
