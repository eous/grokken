"""
JSONL output format for training data.

Handles chunking and formatting for model training.
"""

import json
from pathlib import Path
from typing import Any, Iterator


def chunk_text(
    text: str,
    max_chars: int = 16000,
    overlap_chars: int = 500,
) -> Iterator[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Full text to chunk.
        max_chars: Maximum characters per chunk.
        overlap_chars: Characters to overlap between chunks.

    Yields:
        Text chunks.
    """
    if len(text) <= max_chars:
        yield text
        return

    start = 0
    while start < len(text):
        end = start + max_chars

        # Try to break at paragraph boundary
        if end < len(text):
            # Look for paragraph break near the end
            search_start = max(end - 500, start)
            para_break = text.rfind("\n\n", search_start, end)
            if para_break > start:
                end = para_break + 2  # Include the newlines

        yield text[start:end].strip()

        # Move start, accounting for overlap
        start = end - overlap_chars
        if start >= len(text):
            break


def chunk_for_training(
    text: str,
    barcode: str,
    metadata: dict[str, Any] | None = None,
    max_chars: int = 16000,
    overlap_chars: int = 500,
) -> Iterator[dict[str, Any]]:
    """
    Chunk text and yield training examples.

    Args:
        text: Processed book text.
        barcode: Book identifier.
        metadata: Additional metadata to include.
        max_chars: Maximum characters per chunk.
        overlap_chars: Overlap between chunks.

    Yields:
        Training examples as dicts.
    """
    metadata = metadata or {}

    for i, chunk in enumerate(chunk_text(text, max_chars, overlap_chars)):
        yield {
            "text": chunk,
            "source": {
                "barcode": barcode,
                "chunk_index": i,
                "char_start": i * (max_chars - overlap_chars),  # Approximate
                **metadata,
            },
        }


def save_jsonl(
    records: Iterator[dict[str, Any]] | list[dict[str, Any]],
    output_path: Path | str,
) -> tuple[Path, int]:
    """
    Save records to JSONL format.

    Args:
        records: Iterator or list of dicts to save.
        output_path: Where to save the JSONL file.

    Returns:
        Tuple of (path, record_count).
    """
    output_path = Path(output_path)
    count = 0

    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False))
            f.write("\n")
            count += 1

    return output_path, count


def load_jsonl(path: Path | str) -> Iterator[dict[str, Any]]:
    """
    Load records from JSONL format.

    Args:
        path: Path to JSONL file.

    Yields:
        Parsed dicts.
    """
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
