"""Universal character encoding detector — MIT-licensed rewrite."""

from __future__ import annotations

import warnings

# Import from the Rust implementation
from chardet_rs._chardet_rs import (
    detect as _detect_rs,
    detect_all as _detect_all_rs,
)
from chardet_rs import (
    DEFAULT_MAX_BYTES,
    MINIMUM_THRESHOLD,
    EncodingEra,
    LanguageFilter,
    UniversalDetector,
)
from chardet._version import __version__

__all__ = [
    "DEFAULT_MAX_BYTES",
    "MINIMUM_THRESHOLD",
    "DetectionDict",
    "EncodingEra",
    "LanguageFilter",
    "UniversalDetector",
    "__version__",
    "detect",
    "detect_all",
]

# Type alias for backward compatibility
from typing import TypedDict


class DetectionDict(TypedDict):
    """Dictionary representation of a detection result."""
    encoding: str | None
    confidence: float
    language: str | None


def _warn_deprecated_chunk_size(chunk_size: int, stacklevel: int = 3) -> None:
    """Emit a deprecation warning if chunk_size differs from the default."""
    if chunk_size != 65536:
        warnings.warn(
            "chunk_size is not used in this version of chardet and will be ignored",
            DeprecationWarning,
            stacklevel=stacklevel,
        )


def _validate_max_bytes(max_bytes: int) -> None:
    """Raise ValueError if max_bytes is not a positive integer."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        msg = "max_bytes must be a positive integer"
        raise ValueError(msg)


def detect(
    byte_str: bytes | bytearray,
    should_rename_legacy: bool = True,
    encoding_era: EncodingEra = EncodingEra.ALL,
    chunk_size: int = 65536,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> DetectionDict:
    """Detect the encoding of the given byte string.

    Parameters match chardet 6.x for backward compatibility.
    *chunk_size* is accepted but has no effect.

    :param byte_str: The byte sequence to detect encoding for.
    :param should_rename_legacy: If ``True`` (the default), remap legacy
        encoding names to their modern equivalents.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param chunk_size: Deprecated -- accepted for backward compatibility but
        has no effect.
    :param max_bytes: Maximum number of bytes to examine from *byte_str*.
    :returns: A dictionary with keys ``"encoding"``, ``"confidence"``, and
        ``"language"``.
    """
    _warn_deprecated_chunk_size(chunk_size)
    _validate_max_bytes(max_bytes)
    
    data = byte_str if isinstance(byte_str, bytes) else bytes(byte_str)
    return _detect_rs(
        data,
        should_rename_legacy=should_rename_legacy,
        encoding_era=encoding_era,
        max_bytes=max_bytes,
    )


def detect_all(
    byte_str: bytes | bytearray,
    ignore_threshold: bool = False,
    should_rename_legacy: bool = True,
    encoding_era: EncodingEra = EncodingEra.ALL,
    chunk_size: int = 65536,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[DetectionDict]:
    """Detect all possible encodings of the given byte string.

    Parameters match chardet 6.x for backward compatibility.
    *chunk_size* is accepted but has no effect.

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
    :param chunk_size: Deprecated -- accepted for backward compatibility but
        has no effect.
    :param max_bytes: Maximum number of bytes to examine from *byte_str*.
    :returns: A list of dictionaries, each with keys ``"encoding"``,
        ``"confidence"``, and ``"language"``, sorted by descending confidence.
    """
    _warn_deprecated_chunk_size(chunk_size)
    _validate_max_bytes(max_bytes)
    
    data = byte_str if isinstance(byte_str, bytes) else bytes(byte_str)
    return _detect_all_rs(
        data,
        ignore_threshold=ignore_threshold,
        should_rename_legacy=should_rename_legacy,
        encoding_era=encoding_era,
        max_bytes=max_bytes,
    )
