"""
Typography transforms.

Handles ligatures, quotes, dashes, and other typographic elements
common in historical texts.
"""

import regex as re

# Ligature translation table (str.translate for single-char -> str mapping)
_LIGATURE_TABLE = str.maketrans(
    {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\ufb05": "st",  # Long s + t
        "\ufb06": "st",
        "\ua732": "AA",
        "\ua733": "aa",
        # Æ/æ and Œ/œ are legitimate Unicode characters, not rendering artifacts.
        # They appear in proper nouns (Cæsar), loanwords (œuvre), and historical
        # spellings (mediæval). Expand only in book-specific post_process() if needed.
        "\ua74f": "oo",
        "\u1e9e": "SS",  # Capital eszett
        "\u00df": "ss",
    }
)

# Unicode space translation table: various spaces -> regular space, zero-width -> removed
_SPACE_TABLE = str.maketrans(
    {
        "\u200b": "",  # Zero-width space (remove entirely)
        "\u00a0": " ",  # Non-breaking space
        "\u2002": " ",  # En space
        "\u2003": " ",  # Em space
        "\u2004": " ",  # Three-per-em space
        "\u2005": " ",  # Four-per-em space
        "\u2006": " ",  # Six-per-em space
        "\u2007": " ",  # Figure space
        "\u2008": " ",  # Punctuation space
        "\u2009": " ",  # Thin space
        "\u200a": " ",  # Hair space
        "\u202f": " ",  # Narrow no-break space
        "\u205f": " ",  # Medium mathematical space
        "\u3000": " ",  # Ideographic space
    }
)

# Precompiled regex patterns for normalize_quotes
_RE_DOUBLE_QUOTES = re.compile(r"[\u201c\u201d\u201e\u201f\u00ab\u00bb]")
_RE_SINGLE_QUOTES = re.compile(r"[\u2018\u2019\u201a\u201b]")

# Precompiled regex patterns for normalize_quotes_to_curly
_RE_OPENING_DOUBLE = re.compile(r'(^|[\s\(\[])"', re.MULTILINE)
_RE_CLOSING_DOUBLE = re.compile(r'"')
_RE_CONTRACTION = re.compile(r"(\w)'(\w)")
_RE_OPENING_SINGLE = re.compile(r"(^|[\s\(\[])'", re.MULTILINE)
_RE_CLOSING_SINGLE = re.compile(r"'")

# Precompiled regex patterns for normalize_dashes
_RE_TRIPLE_DASH = re.compile(r"---+")
_RE_DOUBLE_DASH = re.compile(r"--")

# Precompiled regex patterns for normalize_dashes_to_ascii
_RE_ALL_DASHES = re.compile(r"[\u2013\u2014\u2010\u2011\u2012\u2015]")

# Dash character translation table
_DASH_TABLE = str.maketrans(
    {
        "\u2010": "-",  # Unicode hyphen
        "\u2011": "-",  # Non-breaking hyphen
        "\u2012": "\u2013",  # Figure dash -> en dash
        "\u2015": "\u2014",  # Horizontal bar -> em dash
    }
)

# Precompiled regex for normalize_ellipsis
_RE_ELLIPSIS = re.compile(r"\.{3,}")


def fix_ligatures(text: str) -> str:
    """
    Expand typographic ligatures to individual characters.

    Historical texts often contain ligatures that may not render
    correctly or may cause tokenization issues.
    """
    return text.translate(_LIGATURE_TABLE)


def normalize_quotes(text: str) -> str:
    """
    Normalize quotation marks to straight ASCII quotes.

    Useful for consistent tokenization.
    """
    # Double quotes: \u201c \u201d \u201e \u201f \u00ab \u00bb
    text = _RE_DOUBLE_QUOTES.sub('"', text)

    # Single quotes / apostrophes: \u2018 \u2019 \u201a \u201b
    text = _RE_SINGLE_QUOTES.sub("'", text)

    return text


def normalize_quotes_to_curly(text: str) -> str:
    """
    Normalize quotes to proper curly quotes.

    For when you want typographically correct output.
    """
    # Opening double quotes (after whitespace or start of line)
    text = _RE_OPENING_DOUBLE.sub(r"\1\u201c", text)
    # Closing double quotes
    text = _RE_CLOSING_DOUBLE.sub("\u201d", text)

    # Apostrophes in contractions
    text = _RE_CONTRACTION.sub(r"\1\u2019\2", text)
    # Opening single quotes (after whitespace or start of line)
    text = _RE_OPENING_SINGLE.sub(r"\1\u2018", text)
    # Closing single quotes
    text = _RE_CLOSING_SINGLE.sub("\u2019", text)

    return text


def normalize_dashes(text: str) -> str:
    """
    Normalize various dash characters to standard forms.

    - Hyphen (-) for compound words
    - En dash (U+2013) for ranges
    - Em dash (U+2014) for breaks
    """
    # Multiple hyphens to em dash
    text = _RE_TRIPLE_DASH.sub("\u2014", text)
    text = _RE_DOUBLE_DASH.sub("\u2013", text)

    # Normalize various dash characters
    text = text.translate(_DASH_TABLE)

    return text


def normalize_dashes_to_ascii(text: str) -> str:
    """
    Convert all dashes to ASCII hyphen.

    Simpler alternative when you don't need typographic distinction.
    """
    return _RE_ALL_DASHES.sub("-", text)


def normalize_ellipsis(text: str) -> str:
    """Normalize runs of 3+ periods to exactly three periods."""
    # Multiple periods to ellipsis
    text = _RE_ELLIPSIS.sub("...", text)
    return text


def normalize_spaces(text: str) -> str:
    """
    Normalize various space characters to standard space.

    Historical texts may contain various Unicode spaces.
    """
    return text.translate(_SPACE_TABLE)
