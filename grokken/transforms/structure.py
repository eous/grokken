"""
Structural transforms.

Handles page headers, footers, chapter markers, footnotes,
and other structural elements of books.
"""

from collections.abc import Callable

import regex as re

# Precompiled patterns for remove_page_numbers
_RE_DECORATED_PAGE_NUM = re.compile(r"^[\s]*[—–-]\s*\d+\s*[—–-][\s]*$", re.MULTILINE)
_RE_BRACKETED_PAGE_NUM = re.compile(r"^\s*\[\d+\]\s*$", re.MULTILINE)

# Precompiled patterns for remove_footnote_markers
_RE_BRACKET_NUM = re.compile(r"\[\d+\]")
_RE_PAREN_NUM = re.compile(r"\(\d+\)")
_RE_SUPERSCRIPT_NUM = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+")
_RE_SYMBOL_MARKER = re.compile(r"[*†‡§‖¶]+(?=\s|$)")

# Precompiled pattern for extract_footnotes
_RE_FOOTNOTE = re.compile(r"^\d+\.\s+.+$")


def remove_page_headers(pattern: str, flags: int = re.MULTILINE) -> Callable[[str], str]:
    """
    Factory: returns a transform that removes lines matching pattern.

    Args:
        pattern: Regex pattern for header lines to remove.
        flags: Regex flags (default: MULTILINE).

    Returns:
        Transform function that removes matching headers.

    Example:
        remove_page_headers(r"^\\d+\\s+PRINCIPLES OF PSYCHOLOGY\\s*$")
    """
    compiled = re.compile(pattern, flags)

    def transform(text: str) -> str:
        return compiled.sub("", text)

    transform.__doc__ = f"Remove page headers matching: {pattern}"
    return transform


def remove_page_numbers(text: str) -> str:
    """
    Remove standalone page numbers in unambiguous formats.

    Matches decorated and bracketed page number formats:
    - "\u2014 42 \u2014" / "- 42 -"
    - "[42]"

    Does NOT remove plain standalone numbers (e.g. "42" on its own line),
    as these may be years, verse numbers, section numbers, or table data.
    Use book-specific post_process() for plain number removal if needed.
    """
    # Decorated page numbers (must have at least one dash/em-dash decoration)
    text = _RE_DECORATED_PAGE_NUM.sub("", text)

    # Bracketed page numbers
    text = _RE_BRACKETED_PAGE_NUM.sub("", text)

    return text


def remove_running_headers(text: str) -> str:
    """
    Remove common running header patterns.

    These are repeated headers at the top of each page.
    Detects and removes lines that appear frequently with page-like spacing.
    """
    lines = text.split("\n")

    # Count line frequencies (normalized)
    line_counts: dict[str, int] = {}
    for line in lines:
        normalized = line.strip().upper()
        if normalized and len(normalized) < 100:  # Headers are usually short
            line_counts[normalized] = line_counts.get(normalized, 0) + 1

    # Lines appearing 10+ times are likely headers
    header_patterns = {line for line, count in line_counts.items() if count >= 10}

    # Filter out header lines
    filtered = []
    for line in lines:
        if line.strip().upper() not in header_patterns:
            filtered.append(line)

    return "\n".join(filtered)


def detect_chapters(text: str, pattern: str | None = None) -> list[tuple[str, str]]:
    """
    Split text into chapters based on pattern.

    Args:
        text: Full book text.
        pattern: Regex for chapter headings. If None, uses common patterns.

    Returns:
        List of (chapter_title, chapter_text) tuples.
    """
    if pattern is None:
        # Common chapter heading patterns
        pattern = r"^(CHAPTER\s+[IVXLC\d]+\.?.*|Chapter\s+[IVXLC\d]+\.?.*)$"

    chapters = []
    parts = re.split(f"({pattern})", text, flags=re.MULTILINE)

    # parts alternates: [pre-chapter, heading, content, heading, content, ...]
    current_title = "Frontmatter"
    current_text = []

    for i, part in enumerate(parts):
        if re.match(pattern, part.strip(), re.MULTILINE):
            # Save previous chapter
            if current_text:
                chapters.append((current_title, "\n".join(current_text)))
            current_title = part.strip()
            current_text = []
        else:
            current_text.append(part)

    # Don't forget the last chapter
    if current_text:
        chapters.append((current_title, "\n".join(current_text)))

    return chapters


def remove_footnote_markers(text: str) -> str:
    """
    Remove footnote reference markers from body text.

    Handles common formats: [1], (1), *, \u2020, \u2021, \u00a7
    """
    # Numeric markers
    text = _RE_BRACKET_NUM.sub("", text)
    text = _RE_PAREN_NUM.sub("", text)

    # Superscript numbers (if preserved as such)
    text = _RE_SUPERSCRIPT_NUM.sub("", text)

    # Symbol markers
    text = _RE_SYMBOL_MARKER.sub("", text)

    return text


def extract_footnotes(text: str) -> tuple[str, list[str]]:
    """
    Separate footnotes from body text.

    Returns:
        Tuple of (body_text, list_of_footnotes)
    """
    # This is a simplified version - real footnote extraction
    # would need book-specific logic

    lines = text.split("\n")
    body_lines = []
    footnotes = []
    in_footnotes = False

    for line in lines:
        if _RE_FOOTNOTE.match(line.strip()):
            in_footnotes = True
            footnotes.append(line.strip())
        elif in_footnotes and line.startswith(" "):
            # Continuation of footnote (indented line)
            footnotes[-1] += " " + line.strip()
        else:
            in_footnotes = False
            body_lines.append(line)

    return "\n".join(body_lines), footnotes
