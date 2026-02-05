"""
Generation book handlers registry.

Provides per-book handlers for generation Phase 1, similar to how
Phase 0 has per-book processors for text cleaning.
"""

from grokken.generation.books.base import GenerationHandler

# Import all handlers
from grokken.generation.books.principia import PsychologyJamesHandler

# Registry mapping barcode -> handler class
_HANDLERS: dict[str, type[GenerationHandler]] = {
    PsychologyJamesHandler.barcode: PsychologyJamesHandler,
}


def get_handler(barcode: str) -> GenerationHandler | None:
    """
    Get a generation handler for a book by barcode.

    Args:
        barcode: HathiTrust barcode identifier.

    Returns:
        Handler instance if one exists, None otherwise.
    """
    handler_cls = _HANDLERS.get(barcode)
    if handler_cls:
        return handler_cls()
    return None


def has_handler(barcode: str) -> bool:
    """Check if a custom handler exists for this barcode."""
    return barcode in _HANDLERS


def list_handlers() -> list[str]:
    """List all barcodes with custom handlers."""
    return list(_HANDLERS.keys())


__all__ = [
    "GenerationHandler",
    "get_handler",
    "has_handler",
    "list_handlers",
    "PsychologyJamesHandler",
]
