"""Structured logging for security events.

This module provides security-focused logging for audit trails and monitoring.
All security-relevant events are logged with consistent structure for easy
parsing and analysis.

Security: Implements SEC-024 - Structured logging for security events.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any

# Logger name for chardet security events
SECURITY_LOGGER_NAME = "chardet.security"

# Environment variable to enable debug-level security logging
_DEBUG_LOGGING_ENV = "CHARDET_SECURITY_DEBUG"


class SecurityEventType(Enum):
    """Types of security events that can be logged."""

    # Input validation events
    INVALID_INPUT = "invalid_input"
    PARAMETER_VALIDATION_FAILED = "parameter_validation_failed"

    # Resource limit events
    FEED_CALL_LIMIT_EXCEEDED = "feed_call_limit_exceeded"
    MAX_BYTES_LIMIT_EXCEEDED = "max_bytes_limit_exceeded"
    INPUT_SIZE_LIMIT_EXCEEDED = "input_size_limit_exceeded"

    # File operation events
    FILE_ACCESS_DENIED = "file_access_denied"
    SYMLINK_BLOCKED = "symlink_blocked"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"

    # Model/events loading events
    MODEL_LOAD_FAILED = "model_load_failed"
    MODEL_HASH_VERIFICATION_FAILED = "model_hash_verification_failed"
    MODEL_LOADED_SUCCESSFULLY = "model_loaded_successfully"

    # Detection events
    DETECTION_COMPLETED = "detection_completed"
    DETECTION_ERROR = "detection_error"


def _get_security_logger() -> logging.Logger:
    """Get the security logger instance.

    The logger is created on first call to allow runtime configuration.
    """
    logger = logging.getLogger(SECURITY_LOGGER_NAME)

    # Configure on first use if not already configured
    if not logger.handlers and not logger.parent:
        # Default to NullHandler to avoid "no handler" warnings
        logger.addHandler(logging.NullHandler())
        logger.setLevel(
            logging.DEBUG
            if os.environ.get(_DEBUG_LOGGING_ENV, "0") == "1"
            else logging.INFO
        )

    return logger


def log_security_event(
    event_type: SecurityEventType,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    level: int = logging.INFO,
) -> None:
    """Log a structured security event.

    :param event_type: The type of security event.
    :param message: Human-readable description of the event.
    :param details: Additional structured data about the event.
    :param level: Logging level (default: INFO).

    Example::

        log_security_event(
            SecurityEventType.FEED_CALL_LIMIT_EXCEEDED,
            "Feed call limit exceeded",
            details={"feed_count": 1000000, "max_feed_calls": 1000000},
            level=logging.WARNING,
        )
    """
    logger = _get_security_logger()

    # Build structured log record
    # Note: 'message' is reserved in LogRecord, so we use 'event_message'
    extra_data = {
        "event_type": event_type.value,
        "event_message": message,
    }

    if details:
        extra_data["details"] = details

    # Log as structured format
    logger.log(level, f"{event_type.value}: {message}", extra=extra_data)


def log_invalid_input(
    parameter: str | None,
    value: Any,
    reason: str,
) -> None:
    """Log an invalid input validation failure.

    :param parameter: The parameter that failed validation.
    :param value: The invalid value (will be repr'd for safety).
    :param reason: Why the validation failed.
    """
    log_security_event(
        SecurityEventType.INVALID_INPUT,
        f"Invalid input: {reason}",
        details={
            "parameter": parameter,
            "value_repr": repr(value)[:100],  # Truncate for safety
            "reason": reason,
        },
        level=logging.WARNING,
    )


def log_resource_limit(
    limit_type: str,
    current_value: int,
    max_value: int,
    action: str,
) -> None:
    """Log a resource limit event.

    :param limit_type: Type of limit (e.g., "feed_calls", "max_bytes").
    :param current_value: The current value that exceeded the limit.
    :param max_value: The maximum allowed value.
    :param action: The action taken (e.g., "blocked", "warned").
    """
    event_map = {
        "feed_calls": SecurityEventType.FEED_CALL_LIMIT_EXCEEDED,
        "max_bytes": SecurityEventType.MAX_BYTES_LIMIT_EXCEEDED,
        "input_size": SecurityEventType.INPUT_SIZE_LIMIT_EXCEEDED,
    }

    event_type = event_map.get(limit_type, SecurityEventType.INVALID_INPUT)

    log_security_event(
        event_type,
        f"Resource limit exceeded: {limit_type}",
        details={
            "limit_type": limit_type,
            "current_value": current_value,
            "max_value": max_value,
            "action": action,
        },
        level=logging.WARNING,
    )


def log_file_security(
    event_type: SecurityEventType,
    filepath: str,
    reason: str,
) -> None:
    """Log a file security event.

    :param event_type: The type of file security event.
    :param filepath: The file path involved (will be sanitized).
    :param reason: Why the event was triggered.
    """
    # Sanitize filepath - only log basename to avoid leaking paths
    sanitized = os.path.basename(filepath) if filepath else "<unknown>"

    log_security_event(
        event_type,
        f"File security event: {reason}",
        details={
            "filename": sanitized,
            "reason": reason,
        },
        level=logging.WARNING,
    )


def log_model_event(
    event_type: SecurityEventType,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Log a model loading/security event.

    :param event_type: The type of model event.
    :param message: Description of the event.
    :param details: Additional details about the event.
    """
    level = (
        logging.ERROR
        if event_type == SecurityEventType.MODEL_HASH_VERIFICATION_FAILED
        else logging.INFO
    )

    log_security_event(event_type, message, details=details, level=level)


def enable_security_logging(
    handler: logging.Handler | None = None,
    level: int = logging.INFO,
) -> None:
    """Enable security logging with a specific handler.

    :param handler: Log handler to use (default: StreamHandler to stderr).
    :param level: Minimum logging level.

    Example::

        import logging
        from chardet.logging import enable_security_logging

        # Log to stderr
        enable_security_logging()

        # Log to file
        handler = logging.FileHandler("/var/log/chardet-security.log")
        enable_security_logging(handler)
    """
    logger = _get_security_logger()
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    if handler is None:
        handler = logging.StreamHandler()

    # Use a structured format that includes details if present
    class SecurityFormatter(logging.Formatter):
        """Formatter that includes extra details in the log output."""

        def format(self, record: logging.LogRecord) -> str:
            # Build base message
            msg = super().format(record)
            
            # Add details if present
            details = getattr(record, "details", None)
            if details:
                import json
                try:
                    details_str = json.dumps(details)
                    msg = f"{msg} | details={details_str}"
                except (TypeError, ValueError):
                    msg = f"{msg} | details={details!r}"
            
            return msg

    formatter = SecurityFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(event_type)s: %(event_message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def disable_security_logging() -> None:
    """Disable all security logging handlers."""
    logger = _get_security_logger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.addHandler(logging.NullHandler())
