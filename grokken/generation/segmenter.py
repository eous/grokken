"""
Text segmentation for long book processing.

Detects chapter/section boundaries and segments text for
progressive summarization within token budgets.
"""

import re
from dataclasses import dataclass

from openai_harmony import HarmonyEncodingName, load_harmony_encoding

from grokken.generation.config import StrategyConfig
from grokken.generation.schema import Segment


@dataclass
class ChapterMatch:
    """A detected chapter/section heading."""

    title: str
    start_pos: int
    end_pos: int  # End of the heading line
    level: int = 1  # 1 = chapter, 2 = section, etc.


@dataclass
class SegmentationResult:
    """Result of segmenting a book."""

    segments: list[Segment]
    total_tokens: int
    method: str  # "chapter", "section", "token_budget"


# Common chapter heading patterns for historical texts
CHAPTER_PATTERNS = [
    # CHAPTER I, CHAPTER 1, Chapter I, etc.
    r"^(?:CHAPTER|Chapter)\s+([IVXLCDM]+|\d+)(?:\.|:|\s|$)",
    # BOOK I, Book I, etc.
    r"^(?:BOOK|Book)\s+([IVXLCDM]+|\d+)(?:\.|:|\s|$)",
    # PART I, Part I, etc.
    r"^(?:PART|Part)\s+([IVXLCDM]+|\d+)(?:\.|:|\s|$)",
    # SECTION I, Section 1, etc.
    r"^(?:SECTION|Section)\s+([IVXLCDM]+|\d+)(?:\.|:|\s|$)",
    # Numbered sections: I., II., 1., 2., etc. (at start of line)
    r"^([IVXLCDM]+|\d+)\.\s+[A-Z]",
    # All caps headings (likely chapter titles)
    r"^([A-Z][A-Z\s]{10,50})$",
]


class Segmenter:
    """
    Segments books into chapters/sections for progressive summarization.

    Strategy:
    1. Try to detect chapter/section headings
    2. Fall back to token-budget-based splitting at paragraph boundaries
    3. Ensure each segment fits within context limits
    """

    def __init__(
        self,
        strategy_config: StrategyConfig | None = None,
        model: str = "gpt-5.2",
    ):
        """
        Initialize the segmenter.

        Args:
            strategy_config: Configuration with token budgets.
            model: Model name for tokenization (default: gpt-5.2).
        """
        self.config = strategy_config or StrategyConfig()
        self._model = model
        self._encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
        self._chapter_patterns = [re.compile(p, re.MULTILINE) for p in CHAPTER_PATTERNS]

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._encoding.encode(text))

    def detect_chapters(self, text: str) -> list[ChapterMatch]:
        """
        Detect chapter/section headings in text.

        Args:
            text: Full book text.

        Returns:
            List of detected chapter headings with positions.
        """
        chapters = []
        seen_positions = set()

        for pattern in self._chapter_patterns:
            for match in pattern.finditer(text):
                start = match.start()
                # Avoid duplicate detections at same position
                if start in seen_positions:
                    continue

                # Get the full line for the title
                line_start = text.rfind("\n", 0, start) + 1
                line_end = text.find("\n", match.end())
                if line_end == -1:
                    line_end = len(text)

                title = text[line_start:line_end].strip()

                # Skip very short or very long "titles" (probably false positives)
                if len(title) < 3 or len(title) > 100:
                    continue

                chapters.append(
                    ChapterMatch(
                        title=title,
                        start_pos=line_start,
                        end_pos=line_end,
                        level=1,
                    )
                )
                seen_positions.add(start)

        # Sort by position
        chapters.sort(key=lambda c: c.start_pos)

        # Remove duplicates that are too close together (within 100 chars)
        filtered = []
        for chapter in chapters:
            if not filtered or chapter.start_pos - filtered[-1].start_pos > 100:
                filtered.append(chapter)

        return filtered

    def segment_by_chapters(
        self,
        text: str,
        chapters: list[ChapterMatch],
        max_segment_tokens: int | None = None,
    ) -> list[Segment]:
        """
        Create segments based on detected chapters.

        Args:
            text: Full book text.
            chapters: Detected chapter headings.
            max_segment_tokens: Maximum tokens per segment.

        Returns:
            List of Segment objects.
        """
        if max_segment_tokens is None:
            # Default: divide context window by expected number of segments
            max_segment_tokens = self.config.max_context_tokens // 4

        segments = []

        for i, chapter in enumerate(chapters):
            start_char = chapter.start_pos

            # End at next chapter or end of text
            if i + 1 < len(chapters):
                end_char = chapters[i + 1].start_pos
            else:
                end_char = len(text)

            segment_text = text[start_char:end_char]
            token_count = self.count_tokens(segment_text)

            # If segment is too large, we'll need to split it
            if token_count > max_segment_tokens:
                # Split this large chapter into sub-segments
                sub_segments = self._split_large_segment(
                    segment_text,
                    start_char,
                    chapter.title,
                    max_segment_tokens,
                    len(segments),
                )
                segments.extend(sub_segments)
            else:
                segments.append(
                    Segment(
                        index=len(segments),
                        title=chapter.title,
                        start_char=start_char,
                        end_char=end_char,
                        token_count=token_count,
                    )
                )

        return segments

    def segment_by_token_budget(
        self,
        text: str,
        target_tokens_per_segment: int | None = None,
    ) -> list[Segment]:
        """
        Segment text by token budget, splitting at paragraph boundaries.

        Used when chapter detection doesn't find good boundaries.

        Args:
            text: Full book text.
            target_tokens_per_segment: Target tokens per segment.

        Returns:
            List of Segment objects.
        """
        if target_tokens_per_segment is None:
            target_tokens_per_segment = self.config.max_context_tokens // 4

        segments = []
        paragraphs = self._split_paragraphs(text)

        current_start = 0
        current_tokens = 0
        segment_paragraphs = []

        for para_start, para_end, para_text in paragraphs:
            para_tokens = self.count_tokens(para_text)

            # If adding this paragraph exceeds budget, create segment
            if current_tokens + para_tokens > target_tokens_per_segment and segment_paragraphs:
                segments.append(
                    Segment(
                        index=len(segments),
                        title=f"Segment {len(segments) + 1}",
                        start_char=current_start,
                        end_char=segment_paragraphs[-1][1],
                        token_count=current_tokens,
                    )
                )
                current_start = para_start
                current_tokens = 0
                segment_paragraphs = []

            segment_paragraphs.append((para_start, para_end, para_text))
            current_tokens += para_tokens

        # Don't forget the last segment
        if segment_paragraphs:
            segments.append(
                Segment(
                    index=len(segments),
                    title=f"Segment {len(segments) + 1}",
                    start_char=current_start,
                    end_char=segment_paragraphs[-1][1],
                    token_count=current_tokens,
                )
            )

        return segments

    def _split_paragraphs(self, text: str) -> list[tuple[int, int, str]]:
        """
        Split text into paragraphs.

        Returns list of (start_pos, end_pos, text) tuples.
        """
        paragraphs = []
        # Split on double newlines (paragraph breaks)
        pattern = re.compile(r"\n\s*\n")

        last_end = 0
        for match in pattern.finditer(text):
            para_text = text[last_end : match.start()].strip()
            if para_text:
                paragraphs.append((last_end, match.start(), para_text))
            last_end = match.end()

        # Last paragraph
        remaining = text[last_end:].strip()
        if remaining:
            paragraphs.append((last_end, len(text), remaining))

        return paragraphs

    def _split_large_segment(
        self,
        text: str,
        base_start: int,
        base_title: str,
        max_tokens: int,
        base_index: int,
    ) -> list[Segment]:
        """
        Split a large segment into smaller pieces at paragraph boundaries.
        """
        paragraphs = self._split_paragraphs(text)
        segments = []

        current_start = 0
        current_tokens = 0
        segment_paras = []
        part_num = 1

        for para_start, para_end, para_text in paragraphs:
            para_tokens = self.count_tokens(para_text)

            if current_tokens + para_tokens > max_tokens and segment_paras:
                segments.append(
                    Segment(
                        index=base_index + len(segments),
                        title=f"{base_title} (Part {part_num})",
                        start_char=base_start + current_start,
                        end_char=base_start + segment_paras[-1][1],
                        token_count=current_tokens,
                    )
                )
                current_start = para_start
                current_tokens = 0
                segment_paras = []
                part_num += 1

            segment_paras.append((para_start, para_end, para_text))
            current_tokens += para_tokens

        if segment_paras:
            segments.append(
                Segment(
                    index=base_index + len(segments),
                    title=f"{base_title} (Part {part_num})" if part_num > 1 else base_title,
                    start_char=base_start + current_start,
                    end_char=base_start + segment_paras[-1][1],
                    token_count=current_tokens,
                )
            )

        return segments

    def segment(
        self,
        text: str,
        target_segments: int | None = None,
    ) -> SegmentationResult:
        """
        Segment a book using the best available method.

        Tries chapter detection first, falls back to token budget.

        Args:
            text: Full book text.
            target_segments: Target number of segments (optional hint).

        Returns:
            SegmentationResult with segments and metadata.
        """
        total_tokens = self.count_tokens(text)

        # Calculate max tokens per segment based on target
        if target_segments:
            max_segment_tokens = total_tokens // target_segments + 1000  # Buffer
        else:
            max_segment_tokens = self.config.max_context_tokens // 4

        # Try chapter detection first
        chapters = self.detect_chapters(text)

        if len(chapters) >= 3:
            # Good chapter structure detected
            segments = self.segment_by_chapters(text, chapters, max_segment_tokens)
            method = "chapter"
        else:
            # Fall back to token budget
            segments = self.segment_by_token_budget(text, max_segment_tokens)
            method = "token_budget"

        return SegmentationResult(
            segments=segments,
            total_tokens=total_tokens,
            method=method,
        )

    def get_segment_text(self, text: str, segment: Segment) -> str:
        """Extract the text for a segment."""
        return text[segment.start_char : segment.end_char]
