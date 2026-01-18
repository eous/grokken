"""
OCR error correction transforms.

Handles common misreads from optical character recognition,
especially in historical texts with older typefaces.
"""

import regex as re


def fix_common_errors(text: str) -> str:
    """
    Fix frequent OCR misreads.

    These are character-level confusions common across most OCR systems.
    """
    # Word-boundary-aware replacements
    word_replacements = [
        (r"\btbe\b", "the"),
        (r"\bTbe\b", "The"),
        (r"\bwbich\b", "which"),
        (r"\bWbich\b", "Which"),
        (r"\btbat\b", "that"),
        (r"\bTbat\b", "That"),
        (r"\btbis\b", "this"),
        (r"\bTbis\b", "This"),
        (r"\bwitb\b", "with"),
        (r"\bWitb\b", "With"),
        (r"\bfrom\b", "from"),  # Often "frorn"
        (r"\bfrorn\b", "from"),
        (r"\bhave\b", "have"),  # Often "bave"
        (r"\bbave\b", "have"),
    ]

    for pattern, replacement in word_replacements:
        text = re.sub(pattern, replacement, text)

    return text


def fix_rn_to_m(text: str) -> str:
    """
    Fix 'rn' misread as 'm' in common words.

    This is a very common OCR error due to the visual similarity.
    Only applies to known safe words to avoid false positives.
    """
    safe_replacements = [
        (r"\bgovemment\b", "government"),
        (r"\bGovemment\b", "Government"),
        (r"\bcommon\b", "common"),  # Sometimes "cornrnon"
        (r"\bcornrnon\b", "common"),
        (r"\bmodem\b", "modern"),
        (r"\bModem\b", "Modern"),
        (r"\bsumrner\b", "summer"),
        (r"\bSurnrner\b", "Summer"),
    ]

    for pattern, replacement in safe_replacements:
        text = re.sub(pattern, replacement, text)

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
    text = re.sub(r"(?<=[a-zA-Z])1(?=[a-zA-Z])", "l", text)

    # '0' surrounded by lowercase letters -> 'o'
    text = re.sub(r"(?<=[a-z])0(?=[a-z])", "o", text)

    return text


def remove_ocr_artifacts(text: str) -> str:
    """
    Remove common OCR artifacts.

    These are noise patterns that don't represent real text.
    """
    # Random punctuation clusters (likely noise)
    text = re.sub(r"[.,;:]{3,}", "", text)

    # Isolated special characters on their own lines
    text = re.sub(r"^\s*[^\w\s]\s*$", "", text, flags=re.MULTILINE)

    # Repeated characters that are clearly errors (5+ of same char)
    text = re.sub(r"(.)\1{4,}", r"\1\1", text)

    return text


def fix_ff_ligature(text: str) -> str:
    """
    Fix broken ff ligature that appears as 'tf' or 'ft'.

    Common in words like 'different', 'effect', 'offer'.
    """
    safe_words = [
        (r"\bditferent\b", "different"),
        (r"\bDitferent\b", "Different"),
        (r"\betfect\b", "effect"),
        (r"\bEtfect\b", "Effect"),
        (r"\botfer\b", "offer"),
        (r"\bOtfer\b", "Offer"),
        (r"\bsutfer\b", "suffer"),
        (r"\bSutfer\b", "Suffer"),
    ]

    for pattern, replacement in safe_words:
        text = re.sub(pattern, replacement, text)

    return text
