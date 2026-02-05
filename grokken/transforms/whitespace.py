"""
Whitespace and line-handling transforms.

Handles paragraph breaks, line wrapping, hyphenation,
and other whitespace-related issues.
"""

from collections.abc import Callable

import regex as re

# Precompiled patterns for dehyphenate
_RE_DEHYPHENATE = re.compile(r"(\w+)-\n(?:\s*)([a-z])")

# Precompiled patterns for dehyphenate_aggressive
_RE_DEHYPHENATE_AGG = re.compile(r"(\w+)-\s*\n\s*([a-z])")

# Precompiled patterns for normalize_paragraphs
_RE_EXCESS_NEWLINES = re.compile(r"\n{3,}")
_RE_SINGLE_NEWLINE = re.compile(r"(?<=[^\n])\n(?=[^\n])")

# Precompiled patterns for normalize_whitespace
_RE_MULTI_SPACE = re.compile(r" +")
_RE_TRAILING_SPACE = re.compile(r" +$", re.MULTILINE)

# Precompiled pattern for strip_blank_lines
_RE_BLANK_LINE = re.compile(r"^\s*$\n", re.MULTILINE)


def dehyphenate(text: str) -> str:
    """
    Rejoin words split across lines by hyphenation.

    "prin-\\nciples" -> "principles"

    Only joins when the hyphen is at end of line followed by
    lowercase continuation, to avoid breaking intentional hyphens.
    """
    # Hyphen at end of line followed by lowercase letter
    text = _RE_DEHYPHENATE.sub(r"\1\2", text)
    return text


def dehyphenate_aggressive(text: str) -> str:
    """
    More aggressive dehyphenation.

    Also handles cases where there might be spaces after the hyphen
    or before the continuation.
    """
    # Handles hyphens with optional whitespace before/after newline
    text = _RE_DEHYPHENATE_AGG.sub(r"\1\2", text)

    return text


def normalize_paragraphs(text: str) -> str:
    """
    Normalize paragraph breaks.

    - Collapse 3+ newlines to double newline (paragraph break)
    - Single newlines within paragraphs become spaces
    """
    # Collapse excessive newlines
    text = _RE_EXCESS_NEWLINES.sub("\n\n", text)

    # Single newlines -> space (but preserve paragraph breaks)
    # This joins lines within a paragraph
    text = _RE_SINGLE_NEWLINE.sub(" ", text)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace.

    - Tabs to spaces
    - Multiple spaces to single space
    - Trim trailing whitespace from lines
    """
    # Tabs to spaces
    text = text.replace("\t", " ")

    # Multiple spaces to single
    text = _RE_MULTI_SPACE.sub(" ", text)

    # Trailing whitespace
    text = _RE_TRAILING_SPACE.sub("", text)

    # Leading whitespace (optional - might want to preserve indentation)
    # text = re.sub(r"^ +", "", text, flags=re.MULTILINE)

    return text


def strip_blank_lines(text: str) -> str:
    """Remove completely blank lines."""
    return _RE_BLANK_LINE.sub("", text)


def collapse_blank_lines(max_consecutive: int = 2) -> Callable[[str], str]:
    """
    Factory: returns a transform that collapses consecutive blank lines.

    Args:
        max_consecutive: Maximum number of consecutive blank lines to keep.

    Returns:
        Transform function that collapses blank lines.

    Example:
        collapse_blank_lines(max_consecutive=2)
    """
    if max_consecutive < 1:
        raise ValueError(f"max_consecutive must be >= 1, got {max_consecutive}")

    compiled = re.compile(r"(\n\s*){" + str(max_consecutive + 1) + r",}")
    replacement = "\n" * max_consecutive

    def transform(text: str) -> str:
        return compiled.sub(replacement, text)

    transform.__doc__ = f"Collapse blank lines to max {max_consecutive} consecutive"
    return transform


def trim(text: str) -> str:
    """Strip leading and trailing whitespace from entire text."""
    return text.strip()


def unwrap_lines(text: str, min_line_length: int = 60) -> str:
    """
    Unwrap hard-wrapped lines into paragraphs.

    Useful for OCR'd text where each line of the original page
    became a separate line, but paragraphs should flow.

    Args:
        text: Input text with hard line wraps.
        min_line_length: Lines shorter than this at paragraph end
                        are considered paragraph breaks.

    Returns:
        Text with lines unwrapped into paragraphs.
    """
    lines = text.split("\n")
    paragraphs = []
    current_para = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            # Empty line = paragraph break
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
        elif len(stripped) < min_line_length and not stripped.endswith("-"):
            # Short line not ending in hyphen = end of paragraph
            current_para.append(stripped)
            paragraphs.append(" ".join(current_para))
            current_para = []
        else:
            current_para.append(stripped)

    # Don't forget the last paragraph
    if current_para:
        paragraphs.append(" ".join(current_para))

    return "\n\n".join(paragraphs)
