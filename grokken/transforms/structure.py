"""
Structural transforms.

Handles page headers, footers, chapter markers, footnotes,
and other structural elements of books.
"""

import regex as re
from typing import Callable


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
    Remove standalone page numbers.

    Matches common page number formats:
    - "42"
    - "— 42 —"
    - "[42]"
    - "- 42 -"
    """
    # Decorated page numbers
    text = re.sub(r"^[\s]*[—–-]?\s*\d+\s*[—–-]?[\s]*$", "", text, flags=re.MULTILINE)

    # Bracketed page numbers
    text = re.sub(r"^\s*\[\d+\]\s*$", "", text, flags=re.MULTILINE)

    # Plain page numbers on their own line (be careful - might match real content)
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

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

    Handles common formats: [1], (1), *, †, ‡, §
    """
    # Numeric markers
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\(\d+\)", "", text)

    # Superscript numbers (if preserved as such)
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", "", text)

    # Symbol markers
    text = re.sub(r"[*†‡§‖¶]+(?=\s|$)", "", text)

    return text


def extract_footnotes(text: str) -> tuple[str, list[str]]:
    """
    Separate footnotes from body text.

    Returns:
        Tuple of (body_text, list_of_footnotes)
    """
    # This is a simplified version - real footnote extraction
    # would need book-specific logic

    # Look for footnote sections (lines starting with numbers)
    footnote_pattern = r"^\d+\.\s+.+$"

    lines = text.split("\n")
    body_lines = []
    footnotes = []
    in_footnotes = False

    for line in lines:
        if re.match(footnote_pattern, line.strip()):
            in_footnotes = True
            footnotes.append(line.strip())
        elif in_footnotes and line.strip().startswith(" "):
            # Continuation of footnote
            footnotes[-1] += " " + line.strip()
        else:
            in_footnotes = False
            body_lines.append(line)

    return "\n".join(body_lines), footnotes
