# Changelog

All notable changes to chardet-rust are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- **SEC-001**: Added comprehensive input validation at Rust FFI boundary
  - Added `validate_max_bytes()` function with 100 MB limit to prevent memory exhaustion
  - Added `validate_byte_input()` function for input validation
  - All `detect()` and `detect_all()` functions now validate inputs before processing
  - Added `MAX_BYTES_LIMIT` constant (100 MB)

- **SEC-002**: Implemented file size and symlink checks in CLI
  - Added `_validate_file_path()` function with security checks
  - Symlinks are now rejected to prevent symlink attacks
  - File size limited to 50 MB to prevent DoS via large files
  - Directory and special file detection added
  - Added `_MAX_FILE_SIZE` constant (50 MB)

- **SEC-003**: Added iteration limits to `UniversalDetector.feed()`
  - Maximum 1,000,000 feed() calls per detector instance
  - Individual feed() input limited to 50 MB
  - Prevents denial-of-service via excessive iteration
  - Added `MAX_FEED_CALLS` and `MAX_FEED_SIZE` constants

- **SEC-004**: Validated `max_bytes` parameter consistently in Rust
  - Both Rust implementations (`py.rs` and `detector.rs`) now validate max_bytes
  - Consistent error messages across Python and Rust boundaries
  - Zero/negative max_bytes values now properly rejected

- **SEC-011**: Replaced broad exceptions with specific exception types
  - Added custom exception hierarchy in `src/chardet/exceptions.py`:
    - `ChardetError`: Base exception for all chardet errors
    - `DetectionError`: For detection pipeline failures
    - `InvalidInputError`: For input validation failures
    - `ConfigurationError`: For configuration/initialization failures
    - `FileError`: For file operation failures (avoids leaking internal paths)
  - Updated CLI to catch specific exceptions (`ValueError`, `UnicodeDecodeError`, `ChardetError`)
  - Updated model loading to catch specific exceptions (`OSError`, `ImportError`)
  - Error messages no longer expose internal implementation details

### Breaking Changes

- **SEC-010**: Removed deprecated `chunk_size` and `lang_filter` parameters
  - Removed `chunk_size` parameter from `detect()` and `detect_all()` functions
  - Removed `lang_filter` parameter from `UniversalDetector` class
  - Removed deprecation warning code for these parameters
  - These parameters were deprecated and had no effect; their removal simplifies the API

### Changed

- `UniversalDetector` struct (Rust) now tracks `feed_count` and `max_feed_calls`
- CLI file handling now uses `_validate_file_path()` before opening files
- Error messages now include specific limits and thresholds
- Increased `MAX_FEED_SIZE` from 10 MB to 50 MB to support large test files

### Fixed

- Rust `UniversalDetector::new()` now returns `PyResult` to properly propagate validation errors
- CLI no longer exposes internal paths in error messages
- Accuracy tests with large files (~17 MB) now work correctly with increased feed size limit

---

## [0.1.10] - 2026-03-15

### Changed

- Updated security documentation in SECURITY.md
- Added comprehensive security backlog with 15 tracked issues

---

## [0.1.9] - 2026-03-10

### Added

- Performance improvements for bigram model loading
- Enhanced language detection accuracy

---

## [0.1.8] - 2026-03-05

### Fixed

- Fixed UTF-8 detection edge cases with ANSI control bytes
- Improved CJK gating for short inputs

---

## [0.1.7] - 2026-02-28

### Added

- Added encoding era filtering support
- Added language detection for all results

### Changed

- Improved statistical scoring for multi-byte encodings

---

## [0.1.6] - 2026-02-20

### Fixed

- Fixed confusion resolution for ISO-8859 variants
- Improved KOI8-T vs KOI8-R discrimination

---

## [0.1.5] - 2026-02-15

### Added

- Added markup charset extraction for HTML/XML
- Added escape sequence detection (ISO-2022, HZ-GB-2312, UTF-7)

---

## [0.1.4] - 2026-02-10

### Fixed

- Fixed binary detection false positives with UTF-8 multi-byte sequences
- Improved null byte threshold handling

---

## [0.1.3] - 2026-02-05

### Added

- Added UTF-16/32 pattern detection without BOM
- Added structural score caching for performance

---

## [0.1.2] - 2026-01-30

### Fixed

- Fixed legacy encoding name remapping
- Improved Windows-1252 detection accuracy

---

## [0.1.1] - 2026-01-25

### Added

- Added streaming detection with `UniversalDetector`
- Added `detect_all()` for multiple candidate encodings

---

## [0.1.0] - 2026-01-20

### Added

- Initial Rust-powered release
- Multi-stage detection pipeline
- Bigram statistical models
- Python API compatibility with chardet 6.x

---

## Version History Summary

| Version | Release Date | Key Changes |
|---------|-------------|-------------|
| 0.1.10 | 2026-03-15 | Security hardening |
| 0.1.9 | 2026-03-10 | Performance improvements |
| 0.1.8 | 2026-03-05 | UTF-8 edge cases |
| 0.1.7 | 2026-02-28 | Encoding era filtering |
| 0.1.6 | 2026-02-20 | Confusion resolution |
| 0.1.5 | 2026-02-15 | Markup/escape detection |
| 0.1.4 | 2026-02-10 | Binary detection fixes |
| 0.1.3 | 2026-02-05 | UTF-16/32 detection |
| 0.1.2 | 2026-01-30 | Legacy remapping |
| 0.1.1 | 2026-01-25 | Streaming detection |
| 0.1.0 | 2026-01-20 | Initial release |

---

*Last updated: March 15, 2026*
