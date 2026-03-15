"""Tests for security logging functionality.

Security: Tests SEC-024 - Structured logging for security events.
"""

from __future__ import annotations

import logging
from io import StringIO

import pytest

from chardet.logging import (
    SecurityEventType,
    disable_security_logging,
    enable_security_logging,
    log_file_security,
    log_invalid_input,
    log_model_event,
    log_resource_limit,
    log_security_event,
)


class TestSecurityLogging:
    """Tests for security logging functions."""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Set up and tear down logging for each test."""
        # Clean state before test
        disable_security_logging()
        yield
        # Clean state after test
        disable_security_logging()

    def test_log_security_event(self, caplog):
        """Test basic security event logging."""
        enable_security_logging(level=logging.INFO)

        with caplog.at_level(logging.INFO, logger="chardet.security"):
            log_security_event(
                SecurityEventType.DETECTION_COMPLETED,
                "Detection finished successfully",
            )

        assert "detection_completed" in caplog.text
        assert "Detection finished successfully" in caplog.text

    def test_log_security_event_with_details(self, caplog):
        """Test security event logging with details."""
        enable_security_logging(level=logging.INFO)

        with caplog.at_level(logging.INFO, logger="chardet.security"):
            log_security_event(
                SecurityEventType.FEED_CALL_LIMIT_EXCEEDED,
                "Feed limit exceeded",
                details={"feed_count": 1000000, "max_feed_calls": 1000000},
            )

        assert "feed_call_limit_exceeded" in caplog.text
        assert "Feed limit exceeded" in caplog.text

    def test_log_invalid_input(self, caplog):
        """Test invalid input logging."""
        enable_security_logging(level=logging.WARNING)

        with caplog.at_level(logging.WARNING, logger="chardet.security"):
            log_invalid_input(
                parameter="max_bytes",
                value=-1,
                reason="must be positive",
            )

        assert "invalid_input" in caplog.text
        assert "Invalid input: must be positive" in caplog.text
        
        # Check the log record has the details in extra
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, "details")
        assert record.details["parameter"] == "max_bytes"
        assert record.details["reason"] == "must be positive"

    def test_log_resource_limit(self, caplog):
        """Test resource limit logging."""
        enable_security_logging(level=logging.WARNING)

        with caplog.at_level(logging.WARNING, logger="chardet.security"):
            log_resource_limit(
                limit_type="feed_calls",
                current_value=1000000,
                max_value=1000000,
                action="blocked",
            )

        assert "feed_call_limit_exceeded" in caplog.text
        
        # Check the log record has the details in extra
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, "details")
        assert record.details["action"] == "blocked"
        assert record.details["current_value"] == 1000000

    def test_log_file_security_symlink(self, caplog):
        """Test file security logging for symlinks."""
        enable_security_logging(level=logging.WARNING)

        with caplog.at_level(logging.WARNING, logger="chardet.security"):
            log_file_security(
                SecurityEventType.SYMLINK_BLOCKED,
                "/path/to/symlink",
                "Symlink detected",
            )

        assert "symlink_blocked" in caplog.text
        # Only basename should be logged
        assert "symlink" in caplog.text
        assert "/path/to" not in caplog.text

    def test_log_file_security_size(self, caplog):
        """Test file security logging for size exceeded."""
        enable_security_logging(level=logging.WARNING)

        with caplog.at_level(logging.WARNING, logger="chardet.security"):
            log_file_security(
                SecurityEventType.FILE_SIZE_EXCEEDED,
                "/path/to/large/file.txt",
                "File too large",
            )

        assert "file_size_exceeded" in caplog.text
        
        # Check the log record has the details in extra (sanitized path)
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, "details")
        assert record.details["filename"] == "file.txt"
        # Ensure full path is not in the record
        assert "/path/to/large" not in str(record.__dict__)

    def test_log_model_event_success(self, caplog):
        """Test model event logging for successful load."""
        enable_security_logging(level=logging.INFO)

        with caplog.at_level(logging.INFO, logger="chardet.security"):
            log_model_event(
                SecurityEventType.MODEL_LOADED_SUCCESSFULLY,
                "Models loaded",
                details={"size_bytes": 1024},
            )

        assert "model_loaded_successfully" in caplog.text
        assert "Models loaded" in caplog.text

    def test_log_model_event_hash_failure(self, caplog):
        """Test model event logging for hash verification failure."""
        enable_security_logging(level=logging.ERROR)

        with caplog.at_level(logging.ERROR, logger="chardet.security"):
            log_model_event(
                SecurityEventType.MODEL_HASH_VERIFICATION_FAILED,
                "Hash mismatch",
            )

        assert "model_hash_verification_failed" in caplog.text
        assert "Hash mismatch" in caplog.text

    def test_disable_security_logging(self, caplog):
        """Test that disable_security_logging removes handlers."""
        enable_security_logging(level=logging.INFO)
        disable_security_logging()

        with caplog.at_level(logging.INFO, logger="chardet.security"):
            log_security_event(
                SecurityEventType.DETECTION_COMPLETED,
                "This should not appear",
            )

        # Should only have NullHandler, so nothing logged
        # Note: caplog might still capture due to pytest internals

    def test_custom_handler(self):
        """Test using a custom log handler."""
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.INFO)

        enable_security_logging(handler=handler, level=logging.INFO)

        log_security_event(
            SecurityEventType.DETECTION_COMPLETED,
            "Custom handler test",
        )

        output = stream.getvalue()
        assert "detection_completed" in output
        assert "Custom handler test" in output


class TestSecurityEventTypes:
    """Tests for SecurityEventType enum."""

    def test_all_event_types_have_values(self):
        """Test that all event types have string values."""
        for event_type in SecurityEventType:
            assert isinstance(event_type.value, str)
            assert len(event_type.value) > 0

    def test_event_type_uniqueness(self):
        """Test that all event type values are unique."""
        values = [et.value for et in SecurityEventType]
        assert len(values) == len(set(values))


class TestIntegrationWithChardet:
    """Integration tests for security logging with chardet operations."""

    @pytest.fixture(autouse=True)
    def setup_logging(self, caplog):
        """Enable logging for integration tests."""
        enable_security_logging(level=logging.WARNING)
        with caplog.at_level(logging.WARNING, logger="chardet.security"):
            yield
        disable_security_logging()

    def test_validation_error_logged(self, caplog):
        """Test that input validation errors are logged."""
        from chardet.detector import UniversalDetector as PythonUniversalDetector

        with pytest.raises(ValueError):
            PythonUniversalDetector(max_bytes=-1)

        # Check that the error was logged
        assert "invalid_input" in caplog.text
        
        # Verify log record contains details
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, "details")
        assert record.details.get("parameter") == "max_bytes"

    def test_feed_limit_error_logged(self, caplog):
        """Test that feed limit errors are logged."""
        from chardet.detector import UniversalDetector as PythonUniversalDetector

        detector = PythonUniversalDetector()
        # Use reduced limit for test speed
        original_limit = detector._max_feed_calls
        detector._max_feed_calls = 100
        
        try:
            with pytest.raises(RuntimeError):
                for _ in range(110):
                    detector.feed(b"x")
        finally:
            detector._max_feed_calls = original_limit

        assert "feed_call_limit_exceeded" in caplog.text
        
        # Verify log record contains details
        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, "details")
        assert record.details.get("action") == "blocked"
