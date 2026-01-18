"""
Encoding-related transforms.

Handles character encoding issues common in OCR'd historical texts.
"""

import regex as re


def normalize_to_utf8(text: str) -> str:
    """
    Normalize text to clean UTF-8.

    Replaces common encoding artifacts with correct characters.
    """
    replacements = [
        # Windows-1252 artifacts that appear as UTF-8
        ("\x92", "'"),  # Right single quote
        ("\x93", '"'),  # Left double quote
        ("\x94", '"'),  # Right double quote
        ("\x96", "–"),  # En dash
        ("\x97", "—"),  # Em dash
        # Latin-1 artifacts
        ("\xa0", " "),  # Non-breaking space
        ("\xad", ""),   # Soft hyphen
        # Common mojibake
        ("â€™", "'"),
        ("â€œ", '"'),
        ("â€\x9d", '"'),
        ("â€"", "—"),
        ("â€"", "–"),
        ("Ã©", "é"),
        ("Ã¨", "è"),
        ("Ã¢", "â"),
        ("Ã´", "ô"),
        ("Ã®", "î"),
        ("Ã»", "û"),
        ("Ã§", "ç"),
    ]
    for old, new in replacements:
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
            return chr(int(match.group(1), 16))
        except (ValueError, OverflowError):
            return match.group(0)

    return re.sub(r"\\u([0-9a-fA-F]{4})", replace_escape, text)
