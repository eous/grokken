"""
Generation handler for "The Federalist" (1864 reprint).

The Federalist contains a substantial editor's Introduction by Henry B. Dawson
(~246K chars on the publication history and authorship controversy) followed by
56 essays (No. I through No. LXXVI, with gaps due to volume boundaries).

Total ~1.38M chars / ~289K tokens — requires long-book progressive summarization.
"""

import re

from openai_harmony import HarmonyEncodingName, load_harmony_encoding

from grokken.generation.books.base import GenerationHandler
from grokken.generation.schema import Segment


class FederalistHandler(GenerationHandler):
    """Generation handler for The Federalist."""

    barcode = "32044072043805"
    title = "The Federalist"

    # Essay header: "THE FEDERALIST. No. I." (same line) or "THE\n...\nFEDERALIST. No. II."
    # (split across lines with newspaper attribution between THE and FEDERALIST)
    _ESSAY_SAME_LINE = re.compile(r"^THE FEDERALIST\.\s+No\.\s+([IVXLC]+)", re.MULTILINE)
    _ESSAY_SPLIT_LINE = re.compile(r"^THE\n(?:.+\n)?FEDERALIST\.\s+No\.\s+([IVXLC]+)", re.MULTILINE)

    def __init__(self):
        self._encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._encoding.encode(text))

    def get_content_start(self, text: str) -> int:
        """Content starts at INTRODUCTION. (already stripped by Phase 0)."""
        if text.startswith("INTRODUCTION."):
            return 0
        match = re.search(r"^INTRODUCTION\.\s*$", text, re.MULTILINE)
        return match.start() if match else 0

    def get_content_end(self, text: str) -> int:
        """Content ends at END OF VOL. I."""
        match = re.search(r"END OF VOL\.\s*I\.\s*\n", text)
        return match.end() if match else len(text)

    def get_segments(self, text: str) -> list[Segment]:
        """
        Segment the book into Introduction + 56 essays.

        The Introduction is large (~61K tokens) so it gets split into
        sub-segments to stay within context limits. Each essay becomes
        its own segment.
        """
        content_start = self.get_content_start(text)
        content_end = self.get_content_end(text)
        content = text[content_start:content_end]

        # Find all essay positions (two header formats, merged by position)
        essay_positions = []
        for match in self._ESSAY_SAME_LINE.finditer(content):
            essay_positions.append((match.group(1), match.start()))
        for match in self._ESSAY_SPLIT_LINE.finditer(content):
            essay_positions.append((match.group(1), match.start()))
        essay_positions.sort(key=lambda x: x[1])

        segments = []
        seg_index = 0

        # --- Introduction segment(s) ---
        # Introduction runs from start to first essay
        if essay_positions:
            intro_end = essay_positions[0][1]
        else:
            intro_end = len(content)

        intro_text = content[:intro_end]
        intro_tokens = self._count_tokens(intro_text)

        # Split introduction into chunks if it exceeds ~32K tokens
        max_segment_tokens = 32000
        if intro_tokens > max_segment_tokens:
            # Split at paragraph boundaries (double newline)
            paragraphs = intro_text.split("\n\n")
            chunk_texts = []
            current_chunk = []

            for para in paragraphs:
                current_chunk.append(para)
                candidate = "\n\n".join(current_chunk)
                if self._count_tokens(candidate) > max_segment_tokens and len(current_chunk) > 1:
                    # Pop last paragraph, finalize chunk
                    current_chunk.pop()
                    chunk_text = "\n\n".join(current_chunk)
                    chunk_texts.append(chunk_text)
                    current_chunk = [para]

            # Final chunk
            if current_chunk:
                chunk_texts.append("\n\n".join(current_chunk))

            # Create segments for each introduction chunk
            pos = 0
            for i, chunk_text in enumerate(chunk_texts):
                abs_start = content_start + pos
                abs_end = content_start + pos + len(chunk_text)
                part = f" (Part {i + 1}/{len(chunk_texts)})"
                segments.append(
                    Segment(
                        index=seg_index,
                        title=f"Introduction{part}",
                        start_char=abs_start,
                        end_char=abs_end,
                        token_count=self._count_tokens(chunk_text),
                    )
                )
                seg_index += 1
                # Account for the \n\n separator between chunks
                pos += len(chunk_text) + 2
        else:
            # Introduction fits in one segment
            segments.append(
                Segment(
                    index=seg_index,
                    title="Introduction",
                    start_char=content_start,
                    end_char=content_start + intro_end,
                    token_count=intro_tokens,
                )
            )
            seg_index += 1

        # --- Essay segments ---
        for i, (roman, start_pos) in enumerate(essay_positions):
            abs_start = content_start + start_pos

            # End at next essay or end of content
            if i + 1 < len(essay_positions):
                abs_end = content_start + essay_positions[i + 1][1]
            else:
                abs_end = content_end

            segment_text = text[abs_start:abs_end]
            token_count = self._count_tokens(segment_text)

            segments.append(
                Segment(
                    index=seg_index,
                    title=f"Federalist No. {roman}",
                    start_char=abs_start,
                    end_char=abs_end,
                    token_count=token_count,
                )
            )
            seg_index += 1

        return segments

    def preprocess_for_generation(self, text: str) -> str:
        """Keep only main content (Introduction through END OF VOL. I.)."""
        content_start = self.get_content_start(text)
        content_end = self.get_content_end(text)
        return text[content_start:content_end]
