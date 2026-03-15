"""Additional tests for detector coverage.

Covers missing lines in src/chardet/detector.py
"""

from __future__ import annotations

import pytest

from chardet.detector import UniversalDetector, _MAX_FEED_CALLS
from chardet.enums import EncodingEra


class TestUniversalDetectorEdgeCases:
    """Tests for UniversalDetector edge cases."""

    def test_feed_after_done_ignored(self) -> None:
        """Test that feed() is ignored after detector is done."""
        detector = UniversalDetector(max_bytes=10)
        
        # Feed enough data to trigger done
        detector.feed(b"12345678901")  # 11 bytes > 10 max_bytes
        assert detector.done
        
        # This feed should be ignored
        initial_buffer_len = len(detector._buffer)
        detector.feed(b"more data")
        assert len(detector._buffer) == initial_buffer_len

    def test_done_property(self) -> None:
        """Test the done property."""
        detector = UniversalDetector()
        assert not detector.done
        
        detector.feed(b"test data")
        assert not detector.done  # Not done yet
        
        detector.close()
        assert detector.done

    def test_result_before_close(self) -> None:
        """Test result property before close() is called."""
        detector = UniversalDetector()
        
        # Result before close should have empty values
        result = detector.result
        assert "encoding" in result
        assert "confidence" in result
        assert "language" in result
        assert result["confidence"] == 0.0

    def test_result_after_close(self) -> None:
        """Test result property after close() is called."""
        detector = UniversalDetector()
        detector.feed(b"Hello World, this is a test.")
        result = detector.close()
        
        assert "encoding" in result
        assert "confidence" in result
        assert result["confidence"] > 0

    def test_close_idempotent(self) -> None:
        """Test that close() can be called multiple times."""
        detector = UniversalDetector()
        detector.feed(b"test data")
        
        result1 = detector.close()
        result2 = detector.close()  # Second close should be idempotent
        
        assert result1 == result2

    def test_legacymap_property(self) -> None:
        """Test LEGACY_MAP class attribute exists."""
        assert hasattr(UniversalDetector, "LEGACY_MAP")
        # Should be a mapping
        assert "ascii" in UniversalDetector.LEGACY_MAP

    def test_minimum_threshold_property(self) -> None:
        """Test MINIMUM_THRESHOLD class attribute exists."""
        assert hasattr(UniversalDetector, "MINIMUM_THRESHOLD")
        assert isinstance(UniversalDetector.MINIMUM_THRESHOLD, float)


class TestUniversalDetectorFeedLimit:
    """Tests for UniversalDetector feed call limiting."""

    def test_feed_count_incremented(self) -> None:
        """Test that feed count is incremented on each feed."""
        detector = UniversalDetector()
        assert detector._feed_count == 0
        
        detector.feed(b"data1")
        assert detector._feed_count == 1
        
        detector.feed(b"data2")
        assert detector._feed_count == 2

    def test_feed_count_reset(self) -> None:
        """Test that feed count is reset."""
        detector = UniversalDetector()
        
        detector.feed(b"data1")
        detector.feed(b"data2")
        assert detector._feed_count == 2
        
        detector.reset()
        assert detector._feed_count == 0

    def test_feed_limit_enforced_with_small_limit(self) -> None:
        """Test feed limit is enforced with a small limit for speed."""
        detector = UniversalDetector()
        detector._max_feed_calls = 10  # Small limit for testing
        
        # Feed up to limit
        for i in range(10):
            detector.feed(b"x")
        
        # Next feed should raise
        with pytest.raises(RuntimeError, match="Maximum feed\\(\\) calls"):
            detector.feed(b"x")

    def test_max_feed_calls_constant_exists(self) -> None:
        """Test that _MAX_FEED_CALLS constant is defined."""
        assert isinstance(_MAX_FEED_CALLS, int)
        assert _MAX_FEED_CALLS > 0


class TestUniversalDetectorWithBytearray:
    """Tests for UniversalDetector with bytearray input."""

    def test_feed_bytearray(self) -> None:
        """Test feeding bytearray data."""
        detector = UniversalDetector()
        data = bytearray(b"Hello World")
        detector.feed(data)
        result = detector.close()
        assert "encoding" in result


class TestUniversalDetectorWithDifferentEras:
    """Tests for UniversalDetector with different encoding eras."""

    def test_detector_with_modern_web_era(self) -> None:
        """Test detector with MODERN_WEB era."""
        detector = UniversalDetector(encoding_era=EncodingEra.MODERN_WEB)
        detector.feed(b"Hello World")
        result = detector.close()
        assert result["encoding"] is not None

    def test_detector_with_legacy_iso_era(self) -> None:
        """Test detector with LEGACY_ISO era."""
        detector = UniversalDetector(encoding_era=EncodingEra.LEGACY_ISO)
        detector.feed(b"Hello World")
        result = detector.close()
        assert result["encoding"] is not None

    def test_detector_with_all_era(self) -> None:
        """Test detector with ALL era."""
        detector = UniversalDetector(encoding_era=EncodingEra.ALL)
        detector.feed(b"Hello World")
        result = detector.close()
        assert result["encoding"] is not None
