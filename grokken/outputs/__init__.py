"""
Output formatters for processed books.

Handles conversion to various output formats:
- Parquet (intermediate storage)
- JSONL (training data)
"""

from grokken.outputs.parquet import save_parquet, load_parquet
from grokken.outputs.jsonl import save_jsonl, chunk_for_training

__all__ = ["save_parquet", "load_parquet", "save_jsonl", "chunk_for_training"]
