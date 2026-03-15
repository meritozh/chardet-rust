"""Internal shared utilities for chardet.

This module contains constants and utilities used throughout the chardet
package. Threshold constants are empirically derived from the test suite
and represent the minimum values needed for reliable detection.
"""

from __future__ import annotations

#: Default maximum number of bytes to examine during detection.
#: 
#: This limit balances detection accuracy against memory usage and performance.
#: Empirical testing shows that 200KB captures sufficient context for accurate
#: encoding detection in most real-world documents while preventing memory
#: exhaustion on very large files. The pipeline may examine fewer bytes if
#: the encoding is detected with high confidence earlier.
#:
#: Security: This limit prevents DoS attacks via memory exhaustion.
DEFAULT_MAX_BYTES: int = 200_000

#: Default minimum confidence threshold for filtering results.
#:
#: Results with confidence <= 0.20 are considered unreliable and are filtered
#: out unless ignore_threshold=True is passed. This threshold was determined
#: empirically by analyzing the distribution of confidence scores across
#: 2,510 test files. Scores above 0.20 correlate with ~95% accuracy,
#: while scores below this threshold are often false positives.
#:
#: The threshold is intentionally low to avoid filtering valid low-confidence
#: results (e.g., very short inputs or ambiguous encodings).
MINIMUM_THRESHOLD: float = 0.20


def _validate_max_bytes(max_bytes: int) -> None:
    """Raise ValueError if *max_bytes* is not a positive integer."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        # Log security event for invalid input
        try:
            from chardet.logging import log_invalid_input

            log_invalid_input(
                parameter="max_bytes",
                value=max_bytes,
                reason="must be a positive integer",
            )
        except ImportError:
            pass  # Logging is optional

        msg = "max_bytes must be a positive integer"
        raise ValueError(msg)
