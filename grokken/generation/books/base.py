"""
Base class for book-specific generation handlers.

Similar to Phase 0's BookProcessor, these handlers provide
book-specific logic for Phase 1 generation, particularly
for segmentation.
"""

from abc import ABC, abstractmethod

from grokken.generation.schema import Segment


class GenerationHandler(ABC):
    """
    Base class for book-specific generation handling.

    Subclass this to provide custom segmentation logic for books
    where the generic chapter detection doesn't work well.

    Class attributes:
        barcode: HathiTrust barcode identifier (required)
        title: Book title (for documentation)
        front_matter_end: Character position where actual content starts
                         (to skip TOC, title pages, etc.)
    """

    barcode: str = ""
    title: str = ""
    front_matter_end: int = 0

    @abstractmethod
    def get_segments(self, text: str) -> list[Segment]:
        """
        Return the list of segments for this book.

        Args:
            text: Full book text (already cleaned by Phase 0)

        Returns:
            List of Segment objects defining chapter boundaries.
        """
        pass

    def get_content_start(self, text: str) -> int:
        """
        Find where the actual book content starts.

        Override this if front_matter_end needs to be detected dynamically.

        Args:
            text: Full book text.

        Returns:
            Character position where content starts.
        """
        return self.front_matter_end

    def preprocess_for_generation(self, text: str) -> str:
        """
        Optional preprocessing before generation.

        Override to remove/modify content specific to this book
        before summarization (e.g., remove index, appendices).

        Args:
            text: Full book text.

        Returns:
            Preprocessed text.
        """
        return text
