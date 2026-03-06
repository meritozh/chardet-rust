"""Universal character encoding detector — Rust implementation with Python bindings."""

from __future__ import annotations

import importlib.resources
import warnings

from chardet_rs._chardet_rs import (
    EncodingEra,
    LanguageFilter,
    _load_models,
    _models_loaded,
)
from chardet_rs._chardet_rs import UniversalDetector as _UniversalDetectorRs
from chardet_rs._chardet_rs import detect as _detect_rs
from chardet_rs._chardet_rs import detect_all as _detect_all_rs

__version__ = "7.0.0"


# Load bigram models at module initialization
def _init_models():
    """Load statistical bigram models from models.bin."""
    try:
        # Try to load from the chardet package
        ref = importlib.resources.files("chardet.models").joinpath("models.bin")
        if ref.exists():
            data = ref.read_bytes()
            if data:
                _load_models(data)
                return True
    except Exception as e:
        # Models are optional - log error for debugging but don't fail
        import warnings

        warnings.warn(
            f"Failed to load bigram models: {e}", RuntimeWarning, stacklevel=2
        )

    return False


DEFAULT_MAX_BYTES: int = 200_000
MINIMUM_THRESHOLD: float = 0.20
_DEFAULT_CHUNK_SIZE: int = 65_536

# Initialize models (optional - fall back to simplified scoring if not available)
# This must be done after all module-level constants are defined
_init_models()


class DetectionDict(dict):
    """Dictionary representation of a detection result."""


class UniversalDetector:
    """Streaming character encoding detector.

    Implements a feed/close pattern for incremental detection of character
    encoding from byte streams. Compatible with the chardet 6.x API.

    Note: This class is NOT thread-safe. Each thread should create its own
    UniversalDetector instance.
    """

    MINIMUM_THRESHOLD = MINIMUM_THRESHOLD
    LEGACY_MAP = {
        "ascii": "Windows-1252",
        "euc-kr": "CP949",
        "iso-8859-1": "Windows-1252",
        "iso-8859-2": "Windows-1250",
        "iso-8859-5": "Windows-1251",
        "iso-8859-6": "Windows-1256",
        "iso-8859-7": "Windows-1253",
        "iso-8859-8": "Windows-1255",
        "iso-8859-9": "Windows-1254",
        "iso-8859-11": "CP874",
        "iso-8859-13": "Windows-1257",
        "tis-620": "CP874",
    }

    def __init__(
        self,
        lang_filter: LanguageFilter = LanguageFilter.ALL,
        should_rename_legacy: bool = True,
        encoding_era: EncodingEra = EncodingEra.ALL,
        max_bytes: int = DEFAULT_MAX_BYTES,
    ) -> None:
        """Initialize the detector.

        :param lang_filter: Deprecated - accepted for backward compatibility
            but has no effect.
        :param should_rename_legacy: If True (default), remap legacy
            encoding names to their modern equivalents.
        :param encoding_era: Restrict candidate encodings to the given era.
        :param max_bytes: Maximum number of bytes to buffer from feed() calls.
        """
        if lang_filter != LanguageFilter.ALL:
            warnings.warn(
                "lang_filter is not implemented in this version of chardet "
                "and will be ignored",
                DeprecationWarning,
                stacklevel=2,
            )

        self._detector = _UniversalDetectorRs(
            lang_filter=lang_filter,
            should_rename_legacy=should_rename_legacy,
            encoding_era=encoding_era,
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


def detect(
    byte_str: bytes | bytearray,
    should_rename_legacy: bool = True,
    encoding_era: EncodingEra = EncodingEra.ALL,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> DetectionDict:
    """Detect the encoding of the given byte string.

    Parameters match chardet 6.x for backward compatibility.
    *chunk_size* is accepted but has no effect.

    :param byte_str: The byte sequence to detect encoding for.
    :param should_rename_legacy: If True (the default), remap legacy
        encoding names to their modern equivalents.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param chunk_size: Deprecated - accepted for backward compatibility but
        has no effect.
    :param max_bytes: Maximum number of bytes to examine from byte_str.
    :returns: A dictionary with keys "encoding", "confidence", and "language".
    """
    if chunk_size != _DEFAULT_CHUNK_SIZE:
        warnings.warn(
            "chunk_size is not used in this version of chardet and will be ignored",
            DeprecationWarning,
            stacklevel=2,
        )

    if isinstance(byte_str, bytearray):
        byte_str = bytes(byte_str)

    return _detect_rs(
        byte_str,
        should_rename_legacy=should_rename_legacy,
        encoding_era=encoding_era,
        max_bytes=max_bytes,
    )


def detect_all(
    byte_str: bytes | bytearray,
    ignore_threshold: bool = False,
    should_rename_legacy: bool = True,
    encoding_era: EncodingEra = EncodingEra.ALL,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[DetectionDict]:
    """Detect all possible encodings of the given byte string.

    Parameters match chardet 6.x for backward compatibility.
    *chunk_size* is accepted but has no effect.

    When ignore_threshold is False (the default), results with confidence
    <= MINIMUM_THRESHOLD (0.20) are filtered out. If all results are below
    the threshold, the full unfiltered list is returned as a fallback so the
    caller always receives at least one result.

    :param byte_str: The byte sequence to detect encoding for.
    :param ignore_threshold: If True, return all candidate encodings
        regardless of confidence score.
    :param should_rename_legacy: If True (the default), remap legacy
        encoding names to their modern equivalents.
    :param encoding_era: Restrict candidate encodings to the given era.
    :param chunk_size: Deprecated - accepted for backward compatibility but
        has no effect.
    :param max_bytes: Maximum number of bytes to examine from byte_str.
    :returns: A list of dictionaries, each with keys "encoding",
        "confidence", and "language", sorted by descending confidence.
    """
    if chunk_size != _DEFAULT_CHUNK_SIZE:
        warnings.warn(
            "chunk_size is not used in this version of chardet and will be ignored",
            DeprecationWarning,
            stacklevel=2,
        )

    if isinstance(byte_str, bytearray):
        byte_str = bytes(byte_str)

    return _detect_all_rs(
        byte_str,
        ignore_threshold=ignore_threshold,
        should_rename_legacy=should_rename_legacy,
        encoding_era=encoding_era,
        max_bytes=max_bytes,
    )


# Expose enums
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
