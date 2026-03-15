"""Tests for chardet custom exceptions.

Covers exception classes in src/chardet/exceptions.py
"""

from __future__ import annotations

import pytest

from chardet.exceptions import (
    ChardetError,
    ConfigurationError,
    DetectionError,
    FileError,
    InvalidInputError,
)


class TestDetectionError:
    """Tests for DetectionError exception."""

    def test_basic_exception(self) -> None:
        """Test basic DetectionError creation."""
        err = DetectionError("Detection failed")
        assert str(err) == "Detection failed"
        assert err.encoding is None

    def test_exception_with_encoding(self) -> None:
        """Test DetectionError with encoding parameter."""
        err = DetectionError("Detection failed", encoding="utf-8")
        assert str(err) == "Detection failed"
        assert err.encoding == "utf-8"

    def test_is_chardet_error(self) -> None:
        """Test DetectionError is a ChardetError."""
        err = DetectionError("test")
        assert isinstance(err, ChardetError)

    def test_catch_as_base_class(self) -> None:
        """Test catching DetectionError as ChardetError."""
        try:
            raise DetectionError("test error", encoding="latin-1")
        except ChardetError as e:
            assert e.encoding == "latin-1"


class TestInvalidInputError:
    """Tests for InvalidInputError exception."""

    def test_basic_exception(self) -> None:
        """Test basic InvalidInputError creation."""
        err = InvalidInputError("Invalid input")
        assert str(err) == "Invalid input"
        assert err.parameter is None

    def test_exception_with_parameter(self) -> None:
        """Test InvalidInputError with parameter."""
        err = InvalidInputError("Invalid value", parameter="max_bytes")
        assert str(err) == "Invalid value"
        assert err.parameter == "max_bytes"

    def test_is_chardet_error(self) -> None:
        """Test InvalidInputError is a ChardetError."""
        err = InvalidInputError("test")
        assert isinstance(err, ChardetError)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_basic_exception(self) -> None:
        """Test basic ConfigurationError creation."""
        err = ConfigurationError("Config failed")
        assert str(err) == "Config failed"

    def test_is_chardet_error(self) -> None:
        """Test ConfigurationError is a ChardetError."""
        err = ConfigurationError("test")
        assert isinstance(err, ChardetError)


class TestFileError:
    """Tests for FileError exception."""

    def test_basic_exception(self) -> None:
        """Test basic FileError creation."""
        err = FileError("File not found")
        assert str(err) == "File not found"
        assert err.filepath is None

    def test_exception_with_filepath(self) -> None:
        """Test FileError with filepath."""
        err = FileError("Cannot read file", filepath="/path/to/file.txt")
        assert str(err) == "Cannot read file"
        assert err.filepath == "/path/to/file.txt"

    def test_is_chardet_error(self) -> None:
        """Test FileError is a ChardetError."""
        err = FileError("test")
        assert isinstance(err, ChardetError)


class TestChardetErrorHierarchy:
    """Tests for exception hierarchy."""

    def test_all_are_chardet_errors(self) -> None:
        """Test all custom exceptions inherit from ChardetError."""
        exceptions = [
            DetectionError("test"),
            InvalidInputError("test"),
            ConfigurationError("test"),
            FileError("test"),
        ]
        for exc in exceptions:
            assert isinstance(exc, ChardetError)
            assert isinstance(exc, Exception)

    def test_catch_all_with_base_class(self) -> None:
        """Test catching all custom exceptions with ChardetError."""
        raised_exceptions = [
            DetectionError("detection", encoding="utf-8"),
            InvalidInputError("input", parameter="param"),
            ConfigurationError("config"),
            FileError("file", filepath="/path"),
        ]

        for original in raised_exceptions:
            try:
                raise original
            except ChardetError as caught:
                assert type(caught) is type(original)
                assert str(caught) == str(original)
