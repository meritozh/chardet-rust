"""Universal character encoding detector — LGPL-licensed rewrite."""

from __future__ import annotations

from chardet._utils import _validate_max_bytes

# Version info - keep in sync with pyproject.toml
__version__ = "0.1.12"
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
from chardet.universal_detector import UniversalDetector
from chardet_rs import (
    DEFAULT_MAX_BYTES,
    MINIMUM_THRESHOLD,
)

# Import detect functions from Rust implementation
from chardet_rs._chardet_rs import (
    detect as _detect_rs,
)
from chardet_rs._chardet_rs import (
    detect_all as _detect_all_rs,
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


# Type alias for backward compatibility
from typing import TypedDict


class DetectionDict(TypedDict):
    """Dictionary representation of a detection result."""

    encoding: str | None
    confidence: float
    language: str | None


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
