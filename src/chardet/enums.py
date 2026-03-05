"""Enumerations for chardet.

These are re-exported from the Rust implementation.
"""

from __future__ import annotations

# Import from the Rust implementation
from chardet_rs._chardet_rs import EncodingEra, LanguageFilter

__all__ = ["EncodingEra", "LanguageFilter"]
