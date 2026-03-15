"""UniversalDetector — streaming encoding detection.

.. deprecated::
    This module is deprecated. Use :class:`chardet.UniversalDetector` instead,
    which automatically selects the best available backend (Rust or Python).
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chardet.pipeline import DetectionDict

# Emit deprecation warning when this module is imported
warnings.warn(
    "chardet.detector is deprecated. "
    "Use chardet.UniversalDetector instead, which automatically "
    "selects the best available backend (Rust or Python).",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from fallback module
from chardet._fallback import (
    DEFAULT_MAX_BYTES,
    MINIMUM_THRESHOLD,
    UniversalDetector,
    _MAX_FEED_CALLS,
)

__all__ = [
    "DEFAULT_MAX_BYTES",
    "MINIMUM_THRESHOLD",
    "UniversalDetector",
    "_MAX_FEED_CALLS",
]
