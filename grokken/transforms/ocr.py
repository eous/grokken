"""
OCR error correction transforms.

Handles common misreads from optical character recognition,
especially in historical texts with older typefaces.
"""

import regex as re

# Precompiled patterns for fix_common_errors
_COMMON_ERRORS = [
    (re.compile(r"\btbe\b"), "the"),
    (re.compile(r"\bTbe\b"), "The"),
    (re.compile(r"\bwbich\b"), "which"),
    (re.compile(r"\bWbich\b"), "Which"),
    (re.compile(r"\btbat\b"), "that"),
    (re.compile(r"\bTbat\b"), "That"),
    (re.compile(r"\btbis\b"), "this"),
    (re.compile(r"\bTbis\b"), "This"),
    (re.compile(r"\bwitb\b"), "with"),
    (re.compile(r"\bWitb\b"), "With"),
    (re.compile(r"\bfrorn\b"), "from"),
    (re.compile(r"\bbave\b"), "have"),
]

# Precompiled patterns for fix_rn_to_m
_RN_TO_M = [
    (re.compile(r"\bgovemment\b"), "government"),
    (re.compile(r"\bGovemment\b"), "Government"),
    (re.compile(r"\bcommon\b"), "common"),  # Sometimes "cornrnon"
    (re.compile(r"\bcornrnon\b"), "common"),
    (re.compile(r"\bmodem\b"), "modern"),
    (re.compile(r"\bModem\b"), "Modern"),
    (re.compile(r"\bsumrner\b"), "summer"),
    (re.compile(r"\bSurnrner\b"), "Summer"),
]

# Precompiled patterns for fix_digit_letter_confusion
_RE_DIGIT_L = re.compile(r"(?<=[a-zA-Z])1(?=[a-zA-Z])")
_RE_DIGIT_O = re.compile(r"(?<=[a-z])0(?=[a-z])")

# Precompiled patterns for remove_ocr_artifacts
_RE_PUNCT_CLUSTER = re.compile(r"[.,;:]{3,}")
_RE_ISOLATED_SPECIAL = re.compile(r"^\s*[^\w\s]\s*$", re.MULTILINE)
_RE_REPEATED_LETTER = re.compile(r"([a-zA-Z])\1{4,}")

# Precompiled patterns for fix_ff_ligature
_FF_LIGATURE = [
    (re.compile(r"\bditferent\b"), "different"),
    (re.compile(r"\bDitferent\b"), "Different"),
    (re.compile(r"\betfect\b"), "effect"),
    (re.compile(r"\bEtfect\b"), "Effect"),
    (re.compile(r"\botfer\b"), "offer"),
    (re.compile(r"\bOtfer\b"), "Offer"),
    (re.compile(r"\bsutfer\b"), "suffer"),
    (re.compile(r"\bSutfer\b"), "Suffer"),
]


def fix_common_errors(text: str) -> str:
    """
    Fix frequent OCR misreads.

    These are character-level confusions common across most OCR systems.
    """
    for pattern, replacement in _COMMON_ERRORS:
        text = pattern.sub(replacement, text)
    return text


def fix_rn_to_m(text: str) -> str:
    """
    Fix 'rn' misread as 'm' in common words.

    This is a very common OCR error due to the visual similarity.
    Only applies to known safe words to avoid false positives.
    """
    for pattern, replacement in _RN_TO_M:
        text = pattern.sub(replacement, text)
    return text


def fix_long_s(text: str) -> str:
    """
    Fix ſ (long s) common in pre-1800 texts.

    The long s was used in the middle of words until ~1800.
    """
    return text.replace("ſ", "s")


def fix_digit_letter_confusion(text: str) -> str:
    """
    Fix common digit/letter confusions in context.

    - '1' in middle of word is usually 'l'
    - '0' in middle of word is usually 'o'
    - '5' at start of word might be 'S'
    """
    # '1' surrounded by letters -> 'l'
    text = _RE_DIGIT_L.sub("l", text)

    # '0' surrounded by lowercase letters -> 'o'
    text = _RE_DIGIT_O.sub("o", text)

    return text


def remove_ocr_artifacts(text: str) -> str:
    """
    Remove common OCR artifacts.

    These are noise patterns that don't represent real text.
    """
    # Random punctuation clusters (likely noise)
    text = _RE_PUNCT_CLUSTER.sub("", text)

    # Isolated special characters on their own lines
    text = _RE_ISOLATED_SPECIAL.sub("", text)

    # Repeated letters that are clearly errors (5+ of same letter)
    text = _RE_REPEATED_LETTER.sub(r"\1\1", text)

    return text


def fix_ff_ligature(text: str) -> str:
    """
    Fix broken ff ligature that appears as 'tf' or 'ft'.

    Common in words like 'different', 'effect', 'offer'.
    """
    for pattern, replacement in _FF_LIGATURE:
        text = pattern.sub(replacement, text)
    return text
