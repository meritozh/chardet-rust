# Agent Guide for chardet-rust

This guide provides essential information for AI agents working on the chardet-rust project.

## Project Overview

**chardet-rust** is a high-performance character encoding detection library with:
- **Rust core**: Memory-safe detection engine with PyO3 Python bindings
- **Python API**: Compatible with chardet 6.x interface
- **Hybrid implementation**: Pure Python fallback + Rust extension for performance

## Technology Stack

| Component | Technology |
|-----------|------------|
| Core engine | Rust (PyO3) |
| Python API | Python 3.11+ |
| Package manager | `uv` |
| Build system | `setuptools` + `setuptools-rust` |
| Testing | `pytest` |
| Linting | `ruff` |

---

## uv Package Manager Usage

This project uses **`uv`** for fast Python package management. Here are the essential commands:

### Environment Setup

```bash
# Create virtual environment (if not exists)
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Sync dependencies from uv.lock
uv sync

# Sync with dev dependencies
uv sync --group dev

# Sync with docs dependencies
uv sync --group docs
```

### Dependency Management

```bash
# Add a production dependency
uv add <package>

# Add a dev dependency
uv add --group dev <package>

# Add a docs dependency
uv add --group docs <package>

# Update uv.lock after manual pyproject.toml changes
uv lock

# Upgrade all dependencies
uv lock --upgrade
```

### Running Commands

```bash
# Run Python with the project environment
uv run python -c "import chardet; print(chardet.detect(b'hello'))"

# Run pytest
uv run pytest

# Run pytest with specific options
uv run pytest -v --tb=short

# Run ruff linter
uv run ruff check .

# Run ruff formatter
uv run ruff format .

# Run the CLI
uv run chardetect --help
uv run chardetect file.txt
```

### Installing the Package

```bash
# Install in editable mode (development)
uv pip install -e .

# Install with all dev dependencies
uv pip install -e ".[dev]"
```

---

## Build System (Rust + Python)

This project has a Rust extension that must be built:

```bash
# Full build (Rust + Python)
uv pip install -e .

# Or using setuptools directly
python -m build

# For development with auto-rebuild on changes
# (Note: Rust changes require reinstallation)
maturin develop  # If using maturin (not currently used)
```

### Rust Development

```bash
# Navigate to Rust code
cd rust/

# Build Rust library
cargo build --release

# Run Rust tests
cargo test

# Run clippy (Rust linter)
cargo clippy -- -D warnings

# Format Rust code
cargo fmt
```

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=chardet --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_fuzzing.py -v

# Run with parallel execution
uv run pytest -x  # Uses pytest-xdist

# Run only non-benchmark tests
uv run pytest -m "not benchmark"

# Run thread-safety tests (marked as serial)
uv run pytest -m "serial"
```

---

## Code Quality

```bash
# Run ruff linter
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check --fix src/

# Run ruff formatter
uv run ruff format src/

# Type checking (if mypy is configured)
# uv run mypy src/chardet
```

---

## Project Structure

```
chardet-rust/
├── src/
│   ├── chardet/              # Main Python package
│   │   ├── __init__.py       # Public API (detect, detect_all, UniversalDetector)
│   │   ├── detector.py       # Pure Python UniversalDetector
│   │   ├── cli.py            # chardetect command-line tool
│   │   ├── exceptions.py     # Custom exception hierarchy
│   │   ├── pipeline/         # Detection pipeline stages
│   │   └── models/           # Bigram models for statistical detection
│   └── chardet_rs/           # Rust extension Python wrapper
│       └── __init__.py       # Rust-backed implementation
├── rust/                     # Rust source code
│   ├── src/                  # Rust library source
│   ├── Cargo.toml            # Rust dependencies
│   └── tests/                # Rust unit tests
├── tests/                    # Python test suite
├── scripts/                  # Training and utility scripts
├── docs/                     # Sphinx documentation
├── pyproject.toml            # Python project configuration
├── uv.lock                   # uv lock file (commit this!)
└── AGENTS.md                 # This file
```

---

## Key Development Guidelines

### Security

- All security issues are tracked in `SECURITY.md`
- Input validation happens at Python API layer AND Rust FFI boundary
- See `SECURITY.md` for current security posture and backlog

### API Compatibility

- Maintain backward compatibility with chardet 6.x
- `detect()`, `detect_all()`, and `UniversalDetector` are the public API
- Don't change function signatures without deprecation period

### Performance

- The Rust implementation is the performance path
- Pure Python fallback exists for compatibility
- Benchmark changes with `benchmark_demo.py`

### Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all public functions
- Docstrings use Google style (pep257 convention)
- Line length: 88 characters (Black-compatible)

---

## Common Tasks

### Adding a New Feature

1. Implement in Rust (`rust/src/`) if performance-critical
2. Add Python bindings in `rust/src/py.rs`
3. Add pure Python fallback in `src/chardet/` if needed
4. Add tests in `tests/`
5. Update documentation

### Adding a Test

```python
# tests/test_something.py
def test_feature() -> None:
    """Test description."""
    result = chardet.detect(b"test data")
    assert result["encoding"] == "expected"
```

### Updating Documentation

```bash
# Build docs locally
cd docs/
uv run make html

# Serve docs locally
uv run python -m http.server 8000 -d _build/html
```

---

## Troubleshooting

### "No module named 'chardet'"

```bash
# Install the package in editable mode
uv pip install -e .
```

### Rust build errors

```bash
# Ensure Rust toolchain is up to date
rustup update

# Clean and rebuild
cargo clean -p chardet-rs
uv pip install -e .
```

### uv lock file conflicts

```bash
# Regenerate lock file
rm uv.lock
uv lock
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup environment | `uv sync --group dev` |
| Run tests | `uv run pytest` |
| Run linter | `uv run ruff check .` |
| Format code | `uv run ruff format .` |
| Build package | `uv pip install -e .` |
| Run CLI | `uv run chardetect file.txt` |
| Update deps | `uv lock --upgrade` |

---

*Last updated: March 15, 2026*
