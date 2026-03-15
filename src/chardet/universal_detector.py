"""Unified UniversalDetector with smart backend selection.

SEC-020: Consolidates duplicate UniversalDetector implementations.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from chardet._utils import DEFAULT_MAX_BYTES, _validate_max_bytes
from chardet.enums import EncodingEra, _to_rust_encoding_era

if TYPE_CHECKING:
    from chardet.pipeline import DetectionDict

# Try to import Rust implementation
try:
    from chardet_rs._chardet_rs import (
        UniversalDetector as _RustDetector,
    )

    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False


class UniversalDetector:
    """Streaming character encoding detector with automatic backend selection.

    Implements a feed/close pattern for incremental detection of character
    encoding from byte streams. Compatible with the chardet 6.x API.

    This unified implementation automatically selects the best available backend:
    - Rust implementation (fastest, used when available)
    - Pure Python implementation (fallback when Rust is unavailable)

    Example:
        >>> from chardet import UniversalDetector
        >>> detector = UniversalDetector()
        >>> with open('file.txt', 'rb') as f:
        ...     for line in f:
        ...         detector.feed(line)
        ...         if detector.done:
        ...             break
        >>> result = detector.close()
        >>> print(result['encoding'])
        'UTF-8'

    Note:
        This class is NOT thread-safe. Each thread should create its own
        UniversalDetector instance.
    """

    def __init__(
        self,
        should_rename_legacy: bool = True,
        encoding_era: EncodingEra = EncodingEra.ALL,
        max_bytes: int = DEFAULT_MAX_BYTES,
    ) -> None:
        """Initialize the detector.

        :param should_rename_legacy: If True (default), remap legacy
            encoding names to their modern equivalents.
        :param encoding_era: Restrict candidate encodings to the given era.
        :param max_bytes: Maximum number of bytes to buffer from feed() calls.
        :raises ValueError: If max_bytes is not a positive integer.
        """
        _validate_max_bytes(max_bytes)

        if _RUST_AVAILABLE:
            self._backend = _RustDetector(
                should_rename_legacy=should_rename_legacy,
                encoding_era=_to_rust_encoding_era(encoding_era),
                max_bytes=max_bytes,
            )
            self._backend_name = "rust"
        else:
            # Lazy import to avoid circular dependency
            from chardet._fallback import UniversalDetector as _PythonDetector

            self._backend = _PythonDetector(
                should_rename_legacy=should_rename_legacy,
                encoding_era=encoding_era,
                max_bytes=max_bytes,
            )
            self._backend_name = "python"

    def feed(self, byte_str: bytes | bytearray) -> None:
        """Feed a chunk of bytes to the detector.

        Data is accumulated in an internal buffer. Once max_bytes have
        been buffered, done is set to True and further data is ignored
        until reset() is called.

        :param byte_str: The next chunk of bytes to examine.
        :raises ValueError: If called after close() without a reset().
        """
        if isinstance(byte_str, bytearray):
            byte_str = bytes(byte_str)
        self._backend.feed(byte_str)

    def close(self) -> DetectionDict:
        """Finalize detection and return the best result.

        Runs the full detection pipeline on the buffered data.

        :returns: A dictionary with keys "encoding", "confidence", and "language".
        """
        return self._backend.close()

    def reset(self) -> None:
        """Reset the detector to its initial state for reuse."""
        self._backend.reset()

    @property
    def done(self) -> bool:
        """Whether detection is complete and no more data is needed."""
        return self._backend.done

    @property
    def result(self) -> DetectionDict:
        """The current best detection result."""
        return self._backend.result

    @property
    def backend(self) -> str:
        """Return the name of the backend being used ('rust' or 'python')."""
        return self._backend_name
