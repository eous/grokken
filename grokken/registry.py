"""
Registry for auto-discovering book handlers.

Scans the books/ directory for BookProcessor subclasses and
makes them available by barcode or collection name.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Iterator

from grokken.base import BookProcessor


class Registry:
    """
    Registry of book processors.

    Automatically discovers BookProcessor subclasses in the books/ package.
    """

    def __init__(self):
        self._by_barcode: dict[str, type[BookProcessor]] = {}
        self._by_collection: dict[str, list[type[BookProcessor]]] = {}
        self._loaded = False

    def _discover(self) -> None:
        """Scan books/ package for BookProcessor subclasses."""
        if self._loaded:
            return

        # Import the books package
        try:
            import grokken.books as books_pkg
        except ImportError:
            self._loaded = True
            return

        # Walk all submodules
        package_path = Path(books_pkg.__file__).parent

        for importer, modname, ispkg in pkgutil.walk_packages(
            path=[str(package_path)],
            prefix="grokken.books.",
        ):
            try:
                module = importlib.import_module(modname)
            except ImportError as e:
                print(f"Warning: Could not import {modname}: {e}")
                continue

            # Find all BookProcessor subclasses in this module
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BookProcessor)
                    and obj is not BookProcessor
                    and hasattr(obj, "barcode")
                    and obj.barcode  # Has a non-empty barcode
                ):
                    self._register(obj, collection=modname.split(".")[-2] if ispkg else modname.split(".")[-1])

        self._loaded = True

    def _register(self, processor_class: type[BookProcessor], collection: str = "default") -> None:
        """Register a processor class."""
        barcode = processor_class.barcode
        self._by_barcode[barcode] = processor_class

        if collection not in self._by_collection:
            self._by_collection[collection] = []
        self._by_collection[collection].append(processor_class)

    def get(self, barcode: str) -> type[BookProcessor] | None:
        """Get a processor class by barcode."""
        self._discover()
        return self._by_barcode.get(barcode)

    def get_collection(self, name: str) -> list[type[BookProcessor]]:
        """Get all processors in a collection."""
        self._discover()
        return self._by_collection.get(name, [])

    def list_barcodes(self) -> list[str]:
        """List all registered barcodes."""
        self._discover()
        return list(self._by_barcode.keys())

    def list_collections(self) -> list[str]:
        """List all collection names."""
        self._discover()
        return list(self._by_collection.keys())

    def all(self) -> Iterator[type[BookProcessor]]:
        """Iterate over all registered processors."""
        self._discover()
        yield from self._by_barcode.values()

    def __len__(self) -> int:
        self._discover()
        return len(self._by_barcode)

    def __repr__(self) -> str:
        self._discover()
        return f"Registry({len(self)} processors in {len(self._by_collection)} collections)"


# Global registry instance
registry = Registry()
