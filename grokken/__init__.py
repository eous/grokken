"""
grokken - Deep understanding and transformation of historical texts.

The past participle of grok that Heinlein never wrote.
"""

__version__ = "0.1.0"

from grokken.base import BookProcessor

__all__ = ["BookProcessor", "__version__"]


# Lazy import for generation module (requires extra dependencies)
def __getattr__(name: str) -> object:
    if name == "generation":
        from grokken import generation

        return generation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
