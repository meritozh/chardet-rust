"""Universal character encoding detector — LGPL-licensed rewrite."""

from __future__ import annotations

from chardet_rs._chardet_rs import (
    UniversalDetector as _UniversalDetectorRs,
)

# Import from the Rust implementation
from chardet_rs._chardet_rs import (
    detect as _detect_rs,
)
from chardet_rs._chardet_rs import (
    detect_all as _detect_all_rs,
)

from chardet._utils import _validate_max_bytes

# Version info - keep in sync with pyproject.toml
__version__ = "0.1.10"
from chardet.enums import (
    EncodingEra,
    _to_rust_encoding_era,
)
from chardet.exceptions import (
    ChardetError,
    ConfigurationError,
    DetectionError,
    FileError,
    InvalidInputError,
)
from chardet_rs import (
    DEFAULT_MAX_BYTES,
    MINIMUM_THRESHOLD,
)

__all__ = [
    "DEFAULT_MAX_BYTES",
    "MINIMUM_THRESHOLD",
    "ChardetError",
    "ConfigurationError",
    "DetectionDict",
    "DetectionError",
    "EncodingEra",
    "FileError",
    "InvalidInputError",
    "LanguageFilter",
    "UniversalDetector",
    "__version__",
    "detect",
    "detect_all",
    # Logging module is available as chardet.logging
]


class UniversalDetector:
    """Streaming character encoding detector.

    Implements a feed/close pattern for incremental detection of character
    encoding from byte streams. Compatible with the chardet 6.x API.
    """

    MINIMUM_THRESHOLD = MINIMUM_THRESHOLD

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
        """
        _validate_max_bytes(max_bytes)

        self._detector = _UniversalDetectorRs(
            should_rename_legacy=should_rename_legacy,
            encoding_era=_to_rust_encoding_era(encoding_era),
            max_bytes=max_bytes,
        )

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
        self._detector.feed(byte_str)

    def close(self) -> DetectionDict:
        """Finalize detection and return the best result.

        Runs the full detection pipeline on the buffered data.

        :returns: A dictionary with keys "encoding", "confidence", and "language".
        """
        return self._detector.close()

    def reset(self) -> None:
        """Reset the detector to its initial state for reuse."""
        self._detector.reset()

    @property
    def done(self) -> bool:
        """Whether detection is complete and no more data is needed."""
        return self._detector.done

    @property
    def result(self) -> DetectionDict:
        """The current best detection result."""
        return self._detector.result


# Type alias for backward compatibility
from typing import TypedDict


class DetectionDict(TypedDict):
    """Dictionary representation of a detection result."""

    encoding: str | None
    confidence: float
    language: str | None


def _validate_max_bytes(max_bytes: int) -> None:
    """Raise ValueError if max_bytes is not a positive integer."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        msg = "max_bytes must be a positive integer"
        raise ValueError(msg)


def detect(
    byte_str: bytes | bytearray,
    should_rename_legacy: bool = True,
    encoding_era: EncodingEra = EncodingEra.ALL,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> DetectionDict:
    """Detect the encoding of the given byte string.

    Parameters match chardet 6.x for backward compatibility.

    :param byte_str: The byte sequence to detect encoding for.
    :param should_rename_legacy: If ``True`` (the default), remap legacy
        encoding names to their modern equivalents.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param max_bytes: Maximum number of bytes to examine from *byte_str*.
    :returns: A dictionary with keys ``"encoding"``, ``"confidence"``, and
        ``"language"``.
    """
    _validate_max_bytes(max_bytes)

    data = byte_str if isinstance(byte_str, bytes) else bytes(byte_str)
    return _detect_rs(
        data,
        should_rename_legacy=should_rename_legacy,
        encoding_era=_to_rust_encoding_era(encoding_era),
        max_bytes=max_bytes,
    )


def detect_all(
    byte_str: bytes | bytearray,
    ignore_threshold: bool = False,
    should_rename_legacy: bool = True,
    encoding_era: EncodingEra = EncodingEra.ALL,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[DetectionDict]:
    """Detect all possible encodings of the given byte string.

    Parameters match chardet 6.x for backward compatibility.

    When *ignore_threshold* is False (the default), results with confidence
    <= MINIMUM_THRESHOLD (0.20) are filtered out.  If all results are below
    the threshold, the full unfiltered list is returned as a fallback so the
    caller always receives at least one result.

    :param byte_str: The byte sequence to detect encoding for.
    :param ignore_threshold: If ``True``, return all candidate encodings
        regardless of confidence score.
    :param should_rename_legacy: If ``True`` (the default), remap legacy
        encoding names to their modern equivalents.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param max_bytes: Maximum number of bytes to examine from *byte_str*.
    :returns: A list of dictionaries, each with keys ``"encoding"``,
        ``"confidence"``, and ``"language"``, sorted by descending confidence.
    """
    _validate_max_bytes(max_bytes)

    data = byte_str if isinstance(byte_str, bytes) else bytes(byte_str)
    return _detect_all_rs(
        data,
        ignore_threshold=ignore_threshold,
        should_rename_legacy=should_rename_legacy,
        encoding_era=_to_rust_encoding_era(encoding_era),
        max_bytes=max_bytes,
    )
