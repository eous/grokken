"""Tests for BookProcessor base class."""

import pandas as pd
import pytest

from grokken.base import BookProcessor


class SimpleProcessor(BookProcessor):
    """Test processor with simple transforms."""
    barcode = "TEST001"
    title = "Test Book"
    author = "Test Author"

    transforms = [
        str.strip,
        str.lower,
    ]


class TestBookProcessor:
    def test_basic_processing(self):
        proc = SimpleProcessor()
        result = proc.process("  HELLO WORLD  ")
        assert result == "hello world"

    def test_load_from_dataframe(self):
        df = pd.DataFrame([
            {"barcode": "TEST001", "text": "Sample text content"},
            {"barcode": "TEST002", "text": "Other content"},
        ])

        proc = SimpleProcessor()
        raw = proc.load_raw(df)
        assert raw == "Sample text content"

    def test_run_full_pipeline(self):
        df = pd.DataFrame([
            {"barcode": "TEST001", "text": "  PROCESS ME  "},
        ])

        proc = SimpleProcessor()
        result = proc.run(df)
        assert result == "process me"

    def test_stats(self):
        proc = SimpleProcessor()
        proc._raw_text = "HELLO WORLD"
        proc._processed_text = "hello world"

        stats = proc.stats()
        assert stats["barcode"] == "TEST001"
        assert stats["raw_chars"] == 11
        assert stats["processed_chars"] == 11
        assert stats["transforms_applied"] == 2

    def test_missing_barcode_raises(self):
        df = pd.DataFrame([
            {"barcode": "OTHER", "text": "Content"},
        ])

        proc = SimpleProcessor()
        with pytest.raises(ValueError, match="not found"):
            proc.load_raw(df)

    def test_empty_text_raises(self):
        proc = SimpleProcessor()
        with pytest.raises(ValueError, match="No text"):
            proc.process()
