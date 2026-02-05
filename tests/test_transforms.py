"""Tests for transform functions."""


from grokken.transforms import encoding, ocr, structure, typography, whitespace


class TestEncoding:
    def test_normalize_to_utf8_windows_artifacts(self):
        text = "It\x92s a test\x97with dashes"
        result = encoding.normalize_to_utf8(text)
        assert result == "It's a test—with dashes"

    def test_strip_null_bytes(self):
        text = "Hello\x00World"
        assert encoding.strip_null_bytes(text) == "HelloWorld"

    def test_normalize_line_endings(self):
        text = "Line1\r\nLine2\rLine3\n"
        assert encoding.normalize_line_endings(text) == "Line1\nLine2\nLine3\n"


class TestOCR:
    def test_fix_common_errors(self):
        text = "tbe quick brown fox"
        assert ocr.fix_common_errors(text) == "the quick brown fox"

    def test_fix_long_s(self):
        text = "the firſt ſtep"
        assert ocr.fix_long_s(text) == "the first step"

    def test_fix_digit_letter_confusion(self):
        text = "the peop1e"
        assert ocr.fix_digit_letter_confusion(text) == "the people"


class TestTypography:
    def test_fix_ligatures(self):
        text = "ﬁnding the ﬂoor"
        assert typography.fix_ligatures(text) == "finding the floor"

    def test_normalize_quotes(self):
        text = '\u201cHello,\u201d she said, \u2018quietly\u2019'
        assert typography.normalize_quotes(text) == '"Hello," she said, \'quietly\''

    def test_normalize_dashes(self):
        text = "word---word and word--word"
        result = typography.normalize_dashes(text)
        assert "—" in result  # em dash
        assert "–" in result  # en dash


class TestWhitespace:
    def test_dehyphenate(self):
        text = "prin-\nciples of psy-\nchology"
        result = whitespace.dehyphenate(text)
        assert result == "principles of psychology"

    def test_normalize_paragraphs(self):
        text = "Line one\nLine two\n\n\n\nNew paragraph"
        result = whitespace.normalize_paragraphs(text)
        assert "\n\n\n" not in result
        assert "\n\n" in result

    def test_trim(self):
        text = "  \n\nContent here\n\n  "
        assert whitespace.trim(text) == "Content here"


class TestStructure:
    def test_remove_page_headers(self):
        text = "CHAPTER ONE\n\nContent here\n\nCHAPTER ONE\n\nMore content"
        transform = structure.remove_page_headers(r"^CHAPTER ONE$")
        result = transform(text)
        assert "CHAPTER ONE" not in result
        assert "Content here" in result

    def test_remove_page_numbers(self):
        text = "Content\n\n— 42 —\n\nMore content\n\n[123]\n\nEnd"
        result = structure.remove_page_numbers(text)
        assert "42" not in result
        assert "123" not in result
        assert "Content" in result
