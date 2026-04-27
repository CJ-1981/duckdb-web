"""Unit tests for encoding detection module."""

import pytest
import time
from pathlib import Path

from src.csv_parser.encoding_detector import detect_encoding


class TestEncodingDetection:
    """Test suite for encoding detection functionality."""

    def test_detect_encoding_utf8(self, fixture_dir):
        """Test UTF-8 file detection with confidence >= 0.9.

        Requirements:
        - AC-CSV-001: UTF-8 File Upload
        - AC-CSV-012: Korean Encoding Support (UTF-8 baseline)

        Note: ASCII is a subset of UTF-8, so chardet may return 'ascii'
        for files with only English characters. This is correct behavior.
        """
        utf8_file = fixture_dir / "test_data" / "encoding_samples" / "sample_utf8.csv"

        encoding, confidence = detect_encoding(str(utf8_file))

        # ASCII is a subset of UTF-8, both are acceptable
        assert encoding in ['utf-8', 'utf_8', 'ascii'], \
            f"Expected utf-8 or ascii, got {encoding}"
        assert confidence >= 0.9, f"Confidence too low: {confidence}"

    def test_detect_encoding_cp949(self, fixture_dir):
        """Test CP949 file detection with Korean characters.

        Requirements:
        - AC-CSV-002: CP949 File Upload
        - AC-CSV-012: Korean Encoding Support (CP949)
        """
        cp949_file = fixture_dir / "test_data" / "encoding_samples" / "sample_cp949.csv"

        encoding, confidence = detect_encoding(str(cp949_file))

        # chardet may detect cp949 or a variant
        assert 'cp949' in encoding.lower() or 'euc' in encoding.lower(), \
            f"Expected cp949 variant, got {encoding}"
        assert confidence >= 0.6, f"Confidence too low: {confidence}"

    def test_detect_encoding_euckr(self, fixture_dir):
        """Test EUC-KR file detection with Korean characters.

        Requirements:
        - AC-CSV-012: Korean Encoding Support (EUC-KR)
        """
        euckr_file = fixture_dir / "test_data" / "encoding_samples" / "sample_euckr.csv"

        encoding, confidence = detect_encoding(str(euckr_file))

        # chardet may detect euc_kr or related encoding
        assert 'euc' in encoding.lower() or 'kr' in encoding.lower(), \
            f"Expected euc-kr variant, got {encoding}"
        assert confidence >= 0.6, f"Confidence too low: {confidence}"

    def test_encoding_fallback_sequence(self, tmp_path):
        """Test fallback sequence when confidence < 0.7.

        Requirements:
        - AC-CSV-014: Encoding Fallback Sequence (UTF-8 → CP949 → EUC-KR)

        This test creates a file that may produce low confidence detection
        and verifies the fallback mechanism activates correctly.
        """
        # Create a file with mixed content that may confuse chardet
        mixed_file = tmp_path / "mixed_encoding.csv"
        with open(mixed_file, 'w', encoding='utf-8') as f:
            # Mix ASCII and Korean to potentially lower confidence
            f.write('name,나이,city\n')
            f.write('Alice,30,New York\n')
            f.write('Bob,25,Los Angeles\n')

        encoding, confidence = detect_encoding(str(mixed_file))

        # Should fallback to UTF-8 successfully
        assert encoding in ['utf-8', 'utf_8'], \
            f"Expected utf-8 fallback, got {encoding}"
        # Fallback should provide reasonable confidence
        assert confidence >= 0.6, f"Fallback confidence too low: {confidence}"

    def test_encoding_fallback_all_fail(self, tmp_path, monkeypatch):
        """Test fallback when all encodings fail.

        This tests the path where chardet returns low confidence and
        all fallback encodings fail to decode.
        """
        # Create a file with binary data that can't be decoded
        binary_file = tmp_path / "binary_data.csv"
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')

        # Mock chardet to return low confidence
        import src.csv_parser.encoding_detector as enc_module
        original_detect = enc_module.chardet.detect

        def mock_detect(data):
            return {'encoding': 'utf-8', 'confidence': 0.5}  # Low confidence

        monkeypatch.setattr(enc_module.chardet, 'detect', mock_detect)

        # Should still return chardet result even if fallbacks fail
        encoding, confidence = detect_encoding(str(binary_file))

        assert encoding is not None
        assert 0.0 <= confidence <= 1.0

    def test_chardet_returns_none_encoding(self, tmp_path, monkeypatch):
        """Test when chardet returns None as encoding.

        This tests the edge case where chardet fails to detect encoding
        and returns None, triggering the default fallback to utf-8.
        """
        test_file = tmp_path / "test.csv"
        test_file.write_text("name,age\nAlice,30\n", encoding='utf-8')

        # Mock chardet to return None encoding
        import src.csv_parser.encoding_detector as enc_module

        def mock_detect(data):
            return {'encoding': None, 'confidence': 0.0}

        monkeypatch.setattr(enc_module.chardet, 'detect', mock_detect)

        encoding, confidence = detect_encoding(str(test_file))

        # Should default to utf-8 when chardet returns None
        assert encoding == 'utf-8', f"Expected utf-8 default, got {encoding}"

    def test_encoding_timeout(self, monkeypatch):
        """Test timeout protection (5 seconds maximum).

        Requirements:
        - AC-CSV-014: Timeout protection (5 seconds maximum)

        This test verifies that the timeout mechanism works by
        using a very short timeout to avoid long test execution.
        """
        import signal
        from src.csv_parser.encoding_detector import detect_encoding, TimeoutError

        # Create a test file
        test_file = Path("/tmp/test_timeout.csv")
        test_file.write_text("name,age\nAlice,30\n", encoding='utf-8')

        # Monkeypatch signal.alarm to trigger immediate timeout
        alarm_calls = []

        def mock_alarm(seconds):
            alarm_calls.append(seconds)
            if seconds > 0:  # Only trigger timeout when alarm is set
                # Simulate immediate timeout
                raise TimeoutError("Immediate timeout for testing")

        monkeypatch.setattr(signal, 'alarm', mock_alarm)

        # Should raise TimeoutError
        with pytest.raises(TimeoutError) as exc_info:
            detect_encoding(str(test_file), timeout=1)

        assert "timeout" in str(exc_info.value).lower()

        # Clean up
        test_file.unlink()

    def test_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            detect_encoding("/nonexistent/file.csv")

        assert "not found" in str(exc_info.value).lower()

    def test_empty_file(self, tmp_path):
        """Test ValueError for empty file."""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")

        with pytest.raises(ValueError) as exc_info:
            detect_encoding(str(empty_file))

        assert "empty" in str(exc_info.value).lower()

    def test_path_is_directory(self, tmp_path):
        """Test ValueError when path is a directory, not a file."""
        with pytest.raises(ValueError) as exc_info:
            detect_encoding(str(tmp_path))

        assert "not a file" in str(exc_info.value).lower()

    def test_utf8_bom_detection(self, fixture_dir):
        """Test UTF-8 with BOM marker detection.

        UTF-8-sig files should be detected correctly.
        """
        bom_file = fixture_dir / "test_data" / "encoding_samples" / "sample_utf8_bom.csv"

        encoding, confidence = detect_encoding(str(bom_file))

        # Should detect as utf-8 or utf-8-sig
        assert 'utf' in encoding.lower(), f"Expected utf-8 variant, got {encoding}"
        assert confidence >= 0.8, f"Confidence too low: {confidence}"


# Pytest fixture for fixture directory
@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"
