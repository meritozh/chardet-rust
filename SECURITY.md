# Security Policy

This document outlines the security posture of chardet-rust, known security considerations, and planned security improvements.

## Reporting a Vulnerability

If you discover a security vulnerability in chardet-rust, please report it responsibly:

- **Email**: [project maintainers](mailto:info@zopyx.com)
- **GitHub**: Use the [private vulnerability reporting feature](https://github.com/zopyx/chardet-rust/security/advisories/new)

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if available)

We aim to respond within 7 days and will work with you to validate and remediate the issue.

---

## Current Security Posture

### What chardet-rust Does Safely

✅ **Memory safety**: Core detection logic is implemented in Rust, providing memory safety guarantees  
✅ **No network access**: The library operates entirely on local data  
✅ **No code execution**: Input data is analyzed, never executed  
✅ **Input size limits**: Default 200KB limit on examined data  
✅ **Type validation**: Python API validates input types before passing to Rust FFI  

### Known Security Considerations

⚠️ **FFI boundary validation**: Rust side input validation is less strict than Python side  

### Addressed in v0.1.11+

✅ **File handling in CLI**: The `chardetect` CLI validates symlinks, file sizes (50MB limit), and path traversal  
✅ **Rate limiting**: Streaming detector (`UniversalDetector`) has feed call limits (1M calls max) and input size limits (50MB per feed)  
✅ **Model file integrity**: SHA-256 hash verification for `models.bin` in Rust implementation  
✅ **Exception handling**: Broad `except Exception` replaced with specific exception types  
✅ **Structured logging**: Security events logged for audit trails (v0.1.13+)  

---

## Security Backlog

The following security improvements are planned. Items are prioritized by severity and impact.

### 🔴 Critical (Fixed in v0.1.11)

| ID | Issue | Status | Tracking |
|----|-------|--------|----------|
| SEC-001 | Add comprehensive input validation at Rust FFI boundary | ✅ Fixed | v0.1.11 |
| SEC-002 | Implement file size and symlink checks in CLI | ✅ Fixed | v0.1.11 |
| SEC-003 | Add iteration limits to `UniversalDetector.feed()` | ✅ Fixed | v0.1.11 |
| SEC-004 | Validate `max_bytes` parameter consistently in Rust | ✅ Fixed | v0.1.11 |
| SEC-010 | Remove deprecated `chunk_size` and `lang_filter` parameters | ✅ Fixed | v0.1.11 |

### ✅ Completed (v0.1.12)

| ID | Issue | Status | Tracking |
|----|-------|--------|----------|
| SEC-011 | Replace broad `except Exception` with specific exception types | ✅ Fixed | `rust/chardet_rs/__init__.py` |
| SEC-013 | Add feed call limits to pure Python UniversalDetector | ✅ Fixed | `src/chardet/detector.py` |
| SEC-014 | Add fuzzing test suite for malformed input handling | ✅ Fixed | `tests/test_fuzzing.py` |
| SEC-022 | Document empirical basis for threshold constants | ✅ Fixed | `src/chardet/_utils.py` |

### 🟢 Medium Priority (Future Releases)

| ID | Issue | Status | Tracking |
|----|-------|--------|----------|
| SEC-020 | Consolidate duplicate `UniversalDetector` implementations | ✅ Fixed | `src/chardet/universal_detector.py` |

### ✅ Completed (v0.1.13)

| ID | Issue | Status | Tracking |
|----|-------|--------|----------|
| SEC-024 | Implement structured logging for security events | ✅ Fixed | `src/chardet/logging.py` |

### ✅ Completed (Post-v0.1.11)

| ID | Issue | Status | Tracking |
|----|-------|--------|----------|
| SEC-012 | Add cryptographic verification for `models.bin` loading | ✅ Done | Rust implementation |
| SEC-021 | Create custom exception types for encoding detection errors | ✅ Done | `src/chardet/exceptions.py` |
| SEC-023 | Add thread-safety verification tests | ✅ Done | `tests/test_thread_safety.py` |

---

## SEC-020 Consolidation Plan (✅ Completed)

### Implementation (Completed)

The consolidation has been implemented with a unified `UniversalDetector` class:

1. **`chardet.UniversalDetector`** (`src/chardet/universal_detector.py`)
   - Main public API with smart backend selection
   - Automatically selects Rust (preferred) or Python fallback
   - Single entry point for all detection needs

2. **`chardet._fallback.UniversalDetector`** (`src/chardet/_fallback.py`)
   - Pure Python implementation (moved from `chardet.detector`)
   - Used automatically when Rust extension is unavailable
   - Maintains feature parity with Rust version

3. **`chardet_rs.UniversalDetector`** (`src/chardet_rs/__init__.py`)
   - Low-level wrapper around Rust (unchanged)
   - Used internally by the unified implementation

4. **`chardet.detector`** (`src/chardet/detector.py`)
   - **Deprecated** - emits `DeprecationWarning` on import
   - Re-exports from `chardet._fallback` for backward compatibility
   - Will be removed in a future release

### Migration Path

**Current (v0.1.11+)**
```python
# ✅ Recommended - automatic backend selection
from chardet import UniversalDetector

detector = UniversalDetector()
print(detector.backend)  # 'rust' or 'python'
```

```python
# ⚠️ Deprecated - still works but warns
from chardet.detector import UniversalDetector  # DeprecationWarning
```

**Benefits**
- Simpler API - one import path for all use cases
- Automatic performance optimization (Rust when available)
- Graceful degradation (Python fallback)
- Maintains backward compatibility during transition

---

## Security Best Practices for Users

### Safe Usage Patterns

```python
# ✅ Validate file size before detection
import os
from pathlib import Path
import chardet

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def safe_detect_file(filepath: str) -> dict:
    path = Path(filepath)
    
    # Check for symlinks
    if path.is_symlink():
        raise ValueError("Symlinks are not supported")
    
    # Check file size
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes")
    
    with path.open("rb") as f:
        return chardet.detect(f.read())
```

```python
# ✅ Limit streaming detector iterations
from chardet import UniversalDetector

def safe_streaming_detect(file_obj, max_iterations: int = 10000):
    detector = UniversalDetector()
    iterations = 0
    
    for line in file_obj:
        detector.feed(line)
        iterations += 1
        
        if detector.done:
            break
        if iterations >= max_iterations:
            raise RuntimeError("Too many iterations - possible DoS")
    
    return detector.close()
```

### Security Logging (v0.1.13+)

```python
# ✅ Enable security logging for audit trails
import logging
from chardet.logging import enable_security_logging

# Log to stderr
enable_security_logging()

# Or log to file
handler = logging.FileHandler("/var/log/chardet-security.log")
enable_security_logging(handler)

# Now security events are logged:
# - File access blocked (symlinks, size limits)
# - Resource limits exceeded (feed calls, max_bytes)
# - Input validation failures
# - Model loading events
```

### Unsafe Patterns to Avoid

```python
# ❌ Never detect encoding on unvalidated file paths
import chardet
# DANGEROUS: No symlink or size validation
result = chardet.detect(open(user_provided_path, "rb").read())

# ❌ Never use unlimited streaming detection
detector = UniversalDetector()
for line in infinite_stream:  # Could run forever
    detector.feed(line)
```

---

## Security Architecture

### Trust Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                      User Input                              │
│  (potentially malicious byte sequences, file paths)          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Python API Layer                          │
│  - Type validation (_validate_max_bytes)                     │
│  - Deprecation warnings                                      │
│  - Parameter normalization                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PyO3 FFI Boundary                         │
│  - Type conversion (Python → Rust)                           │
│  - ✅ Input validation with MAX_BYTES_LIMIT (100MB)          │
│  - ✅ Empty input and type validation                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Rust Detection Core                        │
│  - Memory-safe pipeline execution                            │
│  - Multi-stage encoding detection                            │
│  - Statistical analysis                                      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Security

1. **Input validation**: Python layer validates types and ranges
2. **Memory safety**: Rust ensures no buffer overflows or use-after-free
3. **Size limits**: Default 200KB limit prevents memory exhaustion
4. **No persistence**: Detected results are not cached or logged

---

## Dependency Security

### Runtime Dependencies

| Dependency | Version | Purpose | Security Review |
|------------|---------|---------|-----------------|
| `pyo3` | 0.23 | Python-Rust bindings | ✅ Actively maintained |
| `once_cell` | 1.19 | Lazy initialization | ✅ Minimal, audited |
| `encoding_rs` | 0.8 | Character encoding | ✅ Mozilla-maintained |

### Development Dependencies

Development dependencies (pytest, ruff, etc.) are not included in production installations and pose minimal risk.

### Dependency Update Policy

- Minor/patch updates: Automated via dependabot
- Major updates: Manual review with changelog analysis
- Security advisories: Immediate review and patch

---

## Security Testing

### Current Test Coverage

- ✅ Unit tests for all pipeline stages
- ✅ Integration tests for API surface
- ✅ Thread safety tests (Python 3.13t)
- ✅ Accuracy tests on 2,510 test files

### Missing Security Tests

- ❌ Fuzzing with malformed input (SEC-014)
- ❌ Property-based testing for edge cases (SEC-014)
- ❌ Resource exhaustion tests
- ❌ Symlink attack tests

### Existing Security Tests

- ✅ Thread-safety tests (`tests/test_thread_safety.py`)
- ✅ Hash verification tests for `models.bin`
- ✅ CLI validation tests for file handling
- ✅ Security logging tests (`tests/test_security_logging.py`)
- ✅ Fuzzing tests for malformed input (`tests/test_fuzzing.py`)

---

## Version Support

| Version | Supported | Security Updates |
|---------|-----------|------------------|
| 0.1.x | ✅ Yes | Critical only |
| < 0.1.0 | ❌ No | None |

Security updates are released as patch versions (e.g., 0.1.1 → 0.1.2).

---

## Security Changelog

### v0.1.13 (In Development)

- **SEC-024**: Implemented structured logging for security events
  - New `chardet.logging` module with security event types
  - Logging for file operations, resource limits, input validation
  - Integration with CLI, UniversalDetector, and model loading

### v0.1.12 (Released)

- **SEC-011**: Replaced broad `except Exception` with specific exception types
- **SEC-013**: Added feed call limits to pure Python `UniversalDetector`
- **SEC-014**: Added comprehensive fuzzing test suite (`tests/test_fuzzing.py`)
- **SEC-022**: Documented empirical basis for threshold constants

### v0.1.11 (Released)

- **SEC-001**: Added comprehensive input validation at Rust FFI boundary
- **SEC-002**: Implemented file size and symlink checks in CLI
- **SEC-003**: Added iteration limits to `UniversalDetector.feed()` (Rust)
- **SEC-004**: Validated `max_bytes` parameter consistently in Rust
- **SEC-010**: Removed deprecated `chunk_size` and `lang_filter` parameters
- **SEC-012**: Added SHA-256 hash verification for `models.bin` loading (Rust)
- **SEC-021**: Created custom exception types (`ChardetError`, `DetectionError`, etc.)
- **SEC-023**: Added thread-safety verification tests

### v0.1.10

- Initial security documentation
- Security backlog established

### v0.1.9 and Earlier

- No formal security tracking

---

## Compliance Considerations

### Licensing

This project is licensed under **LGPL-2.1-or-later**. There is an ongoing licensing dispute regarding the upstream chardet 7.0 AI-assisted rewrite. See [README.md](README.md#license-discussion) for details.

**Legal notice**: This summary is informational only and is not legal advice. Consult legal counsel for compliance questions.

### Data Privacy

chardet-rust:
- Does not collect telemetry
- Does not transmit data externally
- Does not persist input data
- Operates entirely offline

---

## Acknowledgments

Security improvements to this project benefit from community feedback. Contributors who report validated security issues will be acknowledged (with permission) in security advisories.

---

*Last updated: March 15, 2026*

---

## Security Test Coverage

### Fuzzing Tests (`tests/test_fuzzing.py`)

Comprehensive fuzzing tests verify robust handling of:
- **Malformed input**: Invalid byte sequences, incomplete escapes, BOM variants
- **Edge cases**: Empty input, single bytes, all-null/all-0xFF data
- **Resource limits**: Feed call limits, max_bytes boundaries
- **Streaming patterns**: Various chunk sizes and feed patterns
- **Encoding eras**: All eras with edge case inputs

Run fuzzing tests: `pytest tests/test_fuzzing.py -v`
