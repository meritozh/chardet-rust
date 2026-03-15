"""Custom exception hierarchy for chardet.

This module provides specific exception classes for better error handling
and debugging. Using specific exceptions instead of broad ``Exception``
catches helps avoid hiding real errors and provides clearer error messages.
"""

from __future__ import annotations


class ChardetError(Exception):
    """Base exception for all chardet-related errors.

    This is the parent class for all custom exceptions raised by chardet.
    Catching this exception will catch any chardet-specific error.

    Example::

        try:
            result = chardet.detect(data)
        except ChardetError as e:
            print(f"Detection failed: {e}")
    """


class DetectionError(ChardetError):
    """Exception raised when character encoding detection fails.

    This exception is raised when the detection pipeline encounters an
    error during analysis, such as corrupted data or internal processing
    failures.

    :param message: Human-readable error message describing the failure.
    :param encoding: The encoding being detected when the error occurred,
        if known.

    Example::

        try:
            result = chardet.detect(corrupted_data)
        except DetectionError as e:
            print(f"Could not detect encoding: {e}")
    """

    def __init__(self, message: str, encoding: str | None = None) -> None:
        super().__init__(message)
        self.encoding = encoding


class InvalidInputError(ChardetError):
    """Exception raised when input validation fails.

    This exception is raised when the input data or parameters fail
    validation checks, such as invalid byte sequences, unsupported
    parameter values, or type errors.

    :param message: Human-readable error message describing the validation
        failure.
    :param parameter: The name of the parameter that failed validation,
        if applicable.

    Example::

        try:
            result = chardet.detect(data, max_bytes=-1)
        except InvalidInputError as e:
            print(f"Invalid parameter '{e.parameter}': {e}")
    """

    def __init__(self, message: str, parameter: str | None = None) -> None:
        super().__init__(message)
        self.parameter = parameter


class ConfigurationError(ChardetError):
    """Exception raised when configuration or initialization fails.

    This exception is raised when chardet cannot be properly configured
    or initialized, such as when required models cannot be loaded.

    :param message: Human-readable error message describing the configuration
        failure.

    Example::

        try:
            detector = chardet.UniversalDetector()
        except ConfigurationError as e:
            print(f"Configuration failed: {e}")
    """


class FileError(ChardetError):
    """Exception raised when file operations fail.

    This exception is raised when file-related operations fail, such as
    reading a file, checking file permissions, or validating file paths.

    This is a wrapper around OSError that provides chardet-specific
    context and avoids leaking internal paths in error messages.

    :param message: Human-readable error message describing the file error.
    :param filepath: The file path that caused the error, if applicable.

    Example::

        try:
            with open(filepath, "rb") as f:
                data = f.read()
        except FileError as e:
            print(f"File error for '{e.filepath}': {e}")
    """

    def __init__(self, message: str, filepath: str | None = None) -> None:
        super().__init__(message)
        self.filepath = filepath
