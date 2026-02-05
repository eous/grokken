"""
Output formatters for processed books.

Handles conversion to various output formats:
- Parquet (intermediate storage)
- JSONL (training data)
"""

from grokken.outputs.jsonl import chunk_for_training, save_jsonl
from grokken.outputs.parquet import load_parquet, save_parquet

__all__ = ["save_parquet", "load_parquet", "save_jsonl", "chunk_for_training"]
