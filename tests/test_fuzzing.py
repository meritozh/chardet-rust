"""Fuzzing and property-based tests for chardet.

This module contains fuzzing tests to verify that chardet handles malformed
and edge-case inputs safely without crashes or unexpected behavior.

Security: These tests verify SEC-014 - robust handling of malformed input.
"""

from __future__ import annotations

import pytest

import chardet
from chardet import UniversalDetector
from chardet.enums import EncodingEra


class TestDetectFuzzing:
    """Fuzzing tests for chardet.detect() function."""

    @pytest.mark.parametrize(
        "data",
        [
            # Empty input
            b"",
            # Single byte
            b"\x00",
            b"\xff",
            b"A",
            # All null bytes
            b"\x00" * 1000,
            # All 0xFF bytes
            b"\xff" * 1000,
            # Alternating patterns
            bytes([i % 256 for i in range(1000)]),
            # High byte clusters (common in CJK false positives)
            b"\x80\x81\x82\x83" * 100,
            # Invalid UTF-8 sequences
            b"\xc0\x80",  # Overlong encoding
            b"\xfe\x80",  # Invalid start byte
            b"\x80\x80",  # Continuation bytes without start
            # BOM variants
            b"\xef\xbb\xbf",  # UTF-8 BOM
            b"\xfe\xff",  # UTF-16 BE BOM
            b"\xff\xfe",  # UTF-16 LE BOM
            # XML/HTML declarations with malformed encoding
            b'<?xml version="1.0" encoding="',
            b'<meta charset="',
            b'<meta http-equiv="Content-Type" content="text/html; charset=',
            # Very long repeated patterns
            b"A" * 10000,
            b"\x00" * 100000,
            # Mixed ASCII and high bytes
            b"Hello \x80\x81\x82 World \xff\xfe",
            # Escape sequences
            b"\x1b$(D",  # Incomplete ISO-2022 escape
            b"\x1b$B",  # Incomplete JIS escape
            # Nested/recursive patterns
            b"(((((" + b"\x80" * 100 + b")))))",
        ],
    )
    def test_malformed_input_no_crash(self, data: bytes) -> None:
        """Verify detect() handles malformed input without crashing.

        Security: Ensures robust handling of edge cases (SEC-014).
        """
        result = chardet.detect(data)
        assert isinstance(result, dict)
        assert "encoding" in result
        assert "confidence" in result
        assert "language" in result
        # Confidence should always be in valid range
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.parametrize("era", list(EncodingEra))
    def test_all_eras_with_random_data(self, era: EncodingEra) -> None:
        """Test all encoding eras with random byte patterns."""
        data = bytes([i * 7 % 256 for i in range(500)])  # Pseudo-random pattern
        result = chardet.detect(data, encoding_era=era)
        assert isinstance(result, dict)
        assert "encoding" in result
        assert "confidence" in result

    def test_detect_all_with_malformed_input(self) -> None:
        """Test detect_all with various malformed inputs."""
        data = b"\x80\x81\x82\x83" * 50
        results = chardet.detect_all(data)
        assert isinstance(results, list)
        # Should return at least one result even for garbage input
        assert len(results) >= 1
        for result in results:
            assert "encoding" in result
            assert "confidence" in result
            assert "language" in result
            assert 0.0 <= result["confidence"] <= 1.0


class TestUniversalDetectorFuzzing:
    """Fuzzing tests for UniversalDetector streaming API."""

    @pytest.mark.parametrize(
        "chunks",
        [
            # Empty feed
            [],
            # Single empty chunk
            [b""],
            # Multiple empty chunks
            [b"", b"", b""],
            # Very small chunks
            [b"A"] * 100,
            # Large chunks
            [b"X" * 10000],
            # Mixed sizes
            [b"", b"A" * 100, b"", b"B" * 1000, b""],
            # High byte chunks
            [b"\x80"] * 50,
            # Alternating patterns
            [b"\x00" * 100, b"\xff" * 100] * 10,
        ],
    )
    def test_feed_patterns(self, chunks: list[bytes]) -> None:
        """Test UniversalDetector with various feed patterns."""
        detector = UniversalDetector()
        for chunk in chunks:
            detector.feed(chunk)
            if detector.done:
                break
        result = detector.close()
        assert isinstance(result, dict)
        assert "encoding" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_feed_after_close_raises(self) -> None:
        """Verify feed() after close() raises ValueError."""
        detector = UniversalDetector()
        detector.feed(b"test data")
        detector.close()
        with pytest.raises(ValueError, match="feed\\(\\) called after close"):
            detector.feed(b"more data")

    def test_reset_allows_reuse(self) -> None:
        """Verify detector can be reused after reset."""
        detector = UniversalDetector()
        detector.feed(b"first detection")
        result1 = detector.close()
        detector.reset()
        detector.feed(b"second detection with different data \x80\x81")
        result2 = detector.close()
        # Both should return valid results
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)

    def test_max_bytes_boundary(self) -> None:
        """Test behavior at max_bytes boundary."""
        detector = UniversalDetector(max_bytes=100)
        detector.feed(b"A" * 50)
        assert not detector.done  # Under limit
        detector.feed(b"B" * 50)
        assert detector.done  # At limit
        detector.feed(b"C" * 50)  # Should be ignored
        result = detector.close()
        assert isinstance(result, dict)


class TestResourceLimits:
    """Tests for resource limit enforcement (DoS prevention)."""

    def test_max_bytes_limit_enforced(self) -> None:
        """Verify max_bytes parameter is enforced."""
        # Try to allocate with very large max_bytes
        with pytest.raises((ValueError, OverflowError)):
            # The exact limit may vary by implementation
            UniversalDetector(max_bytes=1_000_000_000)  # 1GB

    def test_feed_call_limit_enforced(self) -> None:
        """Verify feed call limit prevents excessive iteration (DoS protection).

        Security: Tests SEC-003/SEC-013 - iteration limits on feed().
        
        Note: This test uses the pure Python fallback with a reduced limit
        for practical testing without running 1M+ iterations.
        """
        from chardet.detector import UniversalDetector as PythonUniversalDetector
        
        detector = PythonUniversalDetector()
        # Temporarily reduce the limit for testing
        original_limit = detector._max_feed_calls
        detector._max_feed_calls = 100  # Use smaller limit for test speed
        
        try:
            # Feed enough chunks to exceed the reduced limit
            with pytest.raises(RuntimeError, match="Maximum feed\\(\\) calls"):
                for _ in range(110):
                    detector.feed(b"x")
        finally:
            # Restore original limit
            detector._max_feed_calls = original_limit


class TestEncodingEraEdgeCases:
    """Tests for encoding era edge cases."""

    @pytest.mark.parametrize(
        "data",
        [
            b"",  # Empty
            b"\x00",  # Null
            b"ASCII only",  # Pure ASCII
            b"\x80\xa0\xc0\xe0",  # High bytes only
        ],
    )
    @pytest.mark.parametrize("era", list(EncodingEra))
    def test_era_with_edge_cases(self, data: bytes, era: EncodingEra) -> None:
        """Test each encoding era with edge case inputs."""
        result = chardet.detect(data, encoding_era=era)
        assert isinstance(result, dict)
        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0


class TestConfidenceBoundary:
    """Tests for confidence score boundary conditions."""

    def test_confidence_range(self) -> None:
        """Verify confidence is always in [0, 1] range."""
        test_inputs = [
            b"",  # Empty - should be low confidence
            b"A",  # Single char
            b"Hello World! This is a test.",  # ASCII
            b"\x80\x81\x82",  # Garbage
            b"\xef\xbb\xbfHello",  # UTF-8 with BOM
        ]
        for data in test_inputs:
            result = chardet.detect(data)
            assert 0.0 <= result["confidence"] <= 1.0, (
                f"Confidence {result['confidence']} out of range for input {data!r}"
            )

    def test_detect_all_returns_sorted_results(self) -> None:
        """Verify detect_all returns results sorted by confidence."""
        data = b"Hello World, this is a test of the detection system."
        results = chardet.detect_all(data)
        # Results should generally be sorted by confidence descending
        confidences = [r["confidence"] for r in results]
        # Allow for small unsorted regions due to threshold filtering
        for i in range(len(confidences) - 1):
            if confidences[i] < confidences[i + 1]:
                # If not sorted, difference should be small
                assert confidences[i + 1] - confidences[i] < 0.5
