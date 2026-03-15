"""Additional tests for _utils coverage.

Covers missing lines in src/chardet/_utils.py
"""

from __future__ import annotations

import pytest

from chardet._utils import DEFAULT_MAX_BYTES, MINIMUM_THRESHOLD, _validate_max_bytes


class TestValidateMaxBytes:
    """Tests for _validate_max_bytes function."""

    def test_valid_positive_integer(self) -> None:
        """Test valid positive integers pass."""
        # Should not raise
        _validate_max_bytes(1)
        _validate_max_bytes(100)
        _validate_max_bytes(DEFAULT_MAX_BYTES)

    def test_zero_rejected(self) -> None:
        """Test zero is rejected."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(0)

    def test_negative_rejected(self) -> None:
        """Test negative numbers are rejected."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(-1)
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(-100)

    def test_bool_rejected(self) -> None:
        """Test booleans are rejected (type check)."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(True)
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(False)

    def test_float_rejected(self) -> None:
        """Test floats are rejected (type check)."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(1.5)

    def test_string_rejected(self) -> None:
        """Test strings are rejected (type check)."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes("100")

    def test_none_rejected(self) -> None:
        """Test None is rejected (type check)."""
        with pytest.raises(ValueError, match="must be a positive integer"):
            _validate_max_bytes(None)


class TestConstants:
    """Tests for module constants."""

    def test_default_max_bytes_is_positive(self) -> None:
        """Test DEFAULT_MAX_BYTES is a positive integer."""
        assert isinstance(DEFAULT_MAX_BYTES, int)
        assert DEFAULT_MAX_BYTES > 0

    def test_minimum_threshold_is_float(self) -> None:
        """Test MINIMUM_THRESHOLD is a float between 0 and 1."""
        assert isinstance(MINIMUM_THRESHOLD, float)
        assert 0.0 <= MINIMUM_THRESHOLD <= 1.0

    def test_default_max_bytes_reasonable(self) -> None:
        """Test DEFAULT_MAX_BYTES is a reasonable value (200KB)."""
        assert DEFAULT_MAX_BYTES == 200_000

    def test_minimum_threshold_reasonable(self) -> None:
        """Test MINIMUM_THRESHOLD is reasonable (0.20)."""
        assert MINIMUM_THRESHOLD == 0.20
