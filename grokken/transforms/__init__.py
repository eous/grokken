"""
Reusable text transforms for book processing.

All transforms are pure functions: str -> str
Some are factories that return transforms: (...) -> (str -> str)

Usage:
    from grokken.transforms import encoding, ocr, typography, structure, whitespace

    transforms = [
        encoding.normalize_to_utf8,
        typography.fix_ligatures,
        whitespace.dehyphenate,
        structure.remove_page_headers(pattern=r"CHAPTER"),
    ]
"""

from grokken.transforms import encoding, ocr, structure, typography, whitespace

__all__ = ["encoding", "ocr", "typography", "structure", "whitespace"]
