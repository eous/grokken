"""
Parquet output format.

Used for intermediate storage of processed books.
"""

from pathlib import Path
from typing import Any

import pandas as pd


def save_parquet(
    records: list[dict[str, Any]],
    output_path: Path | str,
    compression: str = "zstd",
) -> Path:
    """
    Save processed books to parquet.

    Args:
        records: List of dicts with book data (must have 'barcode', 'text').
        output_path: Where to save the parquet file.
        compression: Compression algorithm (zstd, snappy, gzip, none).

    Returns:
        Path to the saved file.
    """
    output_path = Path(output_path)
    df = pd.DataFrame(records)
    df.to_parquet(output_path, index=False, compression=compression)
    return output_path


def load_parquet(path: Path | str) -> pd.DataFrame:
    """
    Load processed books from parquet.

    Args:
        path: Path to parquet file.

    Returns:
        DataFrame with book data.
    """
    return pd.read_parquet(path)
