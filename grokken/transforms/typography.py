"""
Typography transforms.

Handles ligatures, quotes, dashes, and other typographic elements
common in historical texts.
"""

import regex as re


def fix_ligatures(text: str) -> str:
    """
    Expand typographic ligatures to individual characters.

    Historical texts often contain ligatures that may not render
    correctly or may cause tokenization issues.
    """
    ligatures = {
        "ﬀ": "ff",
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬅ": "st",  # Long s + t
        "ﬆ": "st",
        "Ꜳ": "AA",
        "ꜳ": "aa",
        "Æ": "AE",
        "æ": "ae",
        "Œ": "OE",
        "œ": "oe",
        "ꝏ": "oo",
        "ẞ": "SS",  # Capital eszett
        "ß": "ss",
    }
    for lig, expanded in ligatures.items():
        text = text.replace(lig, expanded)
    return text


def normalize_quotes(text: str) -> str:
    """
    Normalize quotation marks to straight ASCII quotes.

    Useful for consistent tokenization.
    """
    # Double quotes
    text = re.sub(r"[""„‟«»]", '"', text)

    # Single quotes / apostrophes
    text = re.sub(r"[''‚‛]", "'", text)

    return text


def normalize_quotes_to_curly(text: str) -> str:
    """
    Normalize quotes to proper curly quotes.

    For when you want typographically correct output.
    """
    # Opening double quotes (after whitespace or start)
    text = re.sub(r'(^|[\s\(\[])"', r"\1"", text)
    # Closing double quotes
    text = re.sub(r'"', """, text)

    # Apostrophes in contractions
    text = re.sub(r"(\w)'(\w)", r"\1'\2", text)
    # Opening single quotes
    text = re.sub(r"(^|[\s\(\[])'", r"\1'", text)
    # Closing single quotes
    text = re.sub(r"'", "'", text)

    return text


def normalize_dashes(text: str) -> str:
    """
    Normalize various dash characters to standard forms.

    - Hyphen (-) for compound words
    - En dash (–) for ranges
    - Em dash (—) for breaks
    """
    # Multiple hyphens to em dash
    text = re.sub(r"---+", "—", text)
    text = re.sub(r"--", "–", text)

    # Normalize various dash characters
    text = text.replace("‐", "-")  # Unicode hyphen
    text = text.replace("‑", "-")  # Non-breaking hyphen
    text = text.replace("‒", "–")  # Figure dash
    text = text.replace("―", "—")  # Horizontal bar

    return text


def normalize_dashes_to_ascii(text: str) -> str:
    """
    Convert all dashes to ASCII hyphen.

    Simpler alternative when you don't need typographic distinction.
    """
    return re.sub(r"[–—‐‑‒―]", "-", text)


def normalize_ellipsis(text: str) -> str:
    """Normalize ellipsis to three periods or Unicode ellipsis."""
    # Multiple periods to ellipsis
    text = re.sub(r"\.{3,}", "...", text)
    return text


def normalize_spaces(text: str) -> str:
    """
    Normalize various space characters to standard space.

    Historical texts may contain various Unicode spaces.
    """
    spaces = [
        "\u00a0",  # Non-breaking space
        "\u2002",  # En space
        "\u2003",  # Em space
        "\u2004",  # Three-per-em space
        "\u2005",  # Four-per-em space
        "\u2006",  # Six-per-em space
        "\u2007",  # Figure space
        "\u2008",  # Punctuation space
        "\u2009",  # Thin space
        "\u200a",  # Hair space
        "\u200b",  # Zero-width space
        "\u202f",  # Narrow no-break space
        "\u205f",  # Medium mathematical space
        "\u3000",  # Ideographic space
    ]
    for space in spaces:
        text = text.replace(space, " ")
    return text
