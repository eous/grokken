"""
Generation handler for William James's "The Principles of Psychology" (1890).

This is Volume II of the work, containing Chapters XVII-XXVIII.
The book has ~391k tokens and requires long-book progressive summarization.

Structure:
- Front matter: Library stamps, title page, table of contents (~7000 chars)
- Main content: 12 chapters (XVII through XXVIII)
- Chapters have varying header formats:
  - Most: "CHAPTER XVII." or "CHAPTER XXI.*"
  - One exception: "CHAPTER XXIII" (no period)
"""

import re

from openai_harmony import HarmonyEncodingName, load_harmony_encoding

from grokken.generation.books.base import GenerationHandler
from grokken.generation.schema import Segment


class PsychologyJamesHandler(GenerationHandler):
    """Generation handler for The Principles of Psychology."""

    barcode = "32044010149714"
    title = "The Principles of Psychology"

    # Chapters in this volume (XVII-XXVIII) with their titles
    CHAPTERS = [
        ("XVII", "SENSATION"),
        ("XVIII", "IMAGINATION"),
        ("XIX", "THE PERCEPTION OF THINGS"),
        ("XX", "THE PERCEPTION OF SPACE"),
        ("XXI", "THE PERCEPTION OF REALITY"),
        ("XXII", "REASONING"),
        ("XXIII", "THE PRODUCTION OF MOVEMENT"),
        ("XXIV", "INSTINCT"),
        ("XXV", "THE EMOTIONS"),
        ("XXVI", "WILL"),
        ("XXVII", "HYPNOTISM"),
        ("XXVIII", "NECESSARY TRUTHS AND THE EFFECTS OF EXPERIENCE"),
    ]

    def __init__(self):
        self._encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._encoding.encode(text))

    def get_content_start(self, text: str) -> int:
        """
        Find where main content starts.

        Note: Phase 0 processing now removes front matter, so content
        typically starts at position 0 with "CHAPTER XVII."
        """
        # Phase 0 now strips front matter, so content starts at 0
        if text.startswith("CHAPTER XVII"):
            return 0

        # Fallback for unprocessed text: look for the marker
        marker = "PSYCHOLOGY.\nCHAPTER XVII."
        pos = text.find(marker)
        if pos > 0:
            return pos + len("PSYCHOLOGY.\n")

        # Another fallback: find first CHAPTER XVII after position 5000
        pattern = r"CHAPTER XVII\.\s*\n\s*SENSATION"
        match = re.search(pattern, text[5000:])
        if match:
            return 5000 + match.start()

        return 0

    def get_content_end(self, text: str) -> int:
        """
        Find where the main content ends (before back matter).

        The book ends with "THE END." followed by INDEX, advertisements,
        and library stamps which should be excluded.
        """
        import re

        # Look for "THE END." which marks the conclusion of Chapter XXVIII
        end_marker = re.search(r"THE END\.\s*\n", text)
        if end_marker:
            return end_marker.end()

        # Fallback: look for INDEX start
        index_marker = re.search(r"^INDEX\.?\s*$", text, re.MULTILINE)
        if index_marker:
            return index_marker.start()

        # Last resort: full text
        return len(text)

    def get_segments(self, text: str) -> list[Segment]:
        """
        Segment the book into its 12 chapters.

        Uses explicit chapter markers with known titles to avoid
        false positives from table of contents entries.
        """
        content_start = self.get_content_start(text)
        content_end = self.get_content_end(text)
        content = text[content_start:content_end]

        segments = []
        chapter_positions = []

        # Find each chapter's position
        for roman, title in self.CHAPTERS:
            # Pattern matches variations:
            # - "CHAPTER XVII." or "CHAPTER XVII.*" or "CHAPTER XXIII" (no period)
            pattern = rf"^CHAPTER\s+{roman}\.?\*?\s*$"

            for match in re.finditer(pattern, content, re.MULTILINE):
                # Verify this is a real chapter by checking title or content follows
                # (title may be missing if removed as a running header during Phase 0)
                after_match = content[match.end():match.end() + 300]

                # Check if title or first word of title appears
                title_found = title in after_match or title.split()[0] in after_match

                # For Chapter XVII (first chapter), accept "inner perception" or "outer perception"
                if roman == "XVII" and ("perception" in after_match.lower()):
                    title_found = True

                # For XXVIII, also accept "final chapter" as indicator (title may be removed)
                if roman == "XXVIII" and "final chapter" in after_match.lower():
                    title_found = True

                if title_found:
                    chapter_positions.append((roman, title, match.start()))
                    break  # Found this chapter, move to next

        # Sort by position (should already be sorted, but just in case)
        chapter_positions.sort(key=lambda x: x[2])

        # Create segments
        for i, (roman, title, start_pos) in enumerate(chapter_positions):
            # Adjust position to absolute
            abs_start = content_start + start_pos

            # End at next chapter or end of content (excluding back matter)
            if i + 1 < len(chapter_positions):
                abs_end = content_start + chapter_positions[i + 1][2]
            else:
                abs_end = content_end

            segment_text = text[abs_start:abs_end]
            token_count = self._count_tokens(segment_text)

            segments.append(
                Segment(
                    index=i,
                    title=f"Chapter {roman}: {title}",
                    start_char=abs_start,
                    end_char=abs_end,
                    token_count=token_count,
                )
            )

        return segments

    def preprocess_for_generation(self, text: str) -> str:
        """
        Remove front and back matter for cleaner generation.

        Keeps only the main chapter content (Chapters XVII-XXVIII).
        Removes:
        - Front matter: Library stamps, title page, table of contents
        - Back matter: Index, advertisements, library stamps
        """
        content_start = self.get_content_start(text)
        content_end = self.get_content_end(text)
        return text[content_start:content_end]
