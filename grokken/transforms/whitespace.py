"""
Whitespace and line-handling transforms.

Handles paragraph breaks, line wrapping, hyphenation,
and other whitespace-related issues.
"""

import regex as re


def dehyphenate(text: str) -> str:
    """
    Rejoin words split across lines by hyphenation.

    "prin-\\nciples" -> "principles"

    Only joins when the hyphen is at end of line followed by
    lowercase continuation, to avoid breaking intentional hyphens.
    """
    # Hyphen at end of line followed by lowercase letter
    text = re.sub(r"(\w+)-\n(\s*)([a-z])", r"\1\3", text)
    return text


def dehyphenate_aggressive(text: str) -> str:
    """
    More aggressive dehyphenation.

    Also handles cases where there might be spaces after the hyphen
    or before the continuation.
    """
    # Standard case
    text = re.sub(r"(\w+)-\s*\n\s*([a-z])", r"\1\2", text)

    # Hyphen followed by space then newline
    text = re.sub(r"(\w+)-\s+\n\s*([a-z])", r"\1\2", text)

    return text


def normalize_paragraphs(text: str) -> str:
    """
    Normalize paragraph breaks.

    - Collapse 3+ newlines to double newline (paragraph break)
    - Single newlines within paragraphs become spaces
    """
    # Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Single newlines -> space (but preserve paragraph breaks)
    # This joins lines within a paragraph
    text = re.sub(r"(?<=[^\n])\n(?=[^\n])", " ", text)

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
    text = re.sub(r" +", " ", text)

    # Trailing whitespace
    text = re.sub(r" +$", "", text, flags=re.MULTILINE)

    # Leading whitespace (optional - might want to preserve indentation)
    # text = re.sub(r"^ +", "", text, flags=re.MULTILINE)

    return text


def strip_blank_lines(text: str) -> str:
    """Remove completely blank lines."""
    return re.sub(r"^\s*$\n", "", text, flags=re.MULTILINE)


def collapse_blank_lines(text: str, max_consecutive: int = 2) -> str:
    """
    Collapse consecutive blank lines.

    Args:
        text: Input text.
        max_consecutive: Maximum number of consecutive blank lines to keep.

    Returns:
        Text with blank lines collapsed.
    """
    pattern = r"(\n\s*){" + str(max_consecutive + 1) + r",}"
    replacement = "\n" * max_consecutive
    return re.sub(pattern, replacement, text)


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
