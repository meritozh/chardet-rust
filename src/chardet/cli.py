"""Command-line interface for chardet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chardet
from chardet._utils import DEFAULT_MAX_BYTES
from chardet.enums import EncodingEra
from chardet.exceptions import ChardetError, DetectionError, FileError
from chardet.logging import SecurityEventType, log_file_security
from chardet.pipeline import DetectionDict

# Hardcoded list since Rust enum doesn't support Python enum iteration
_ERA_NAMES = [
    "modern_web",
    "legacy_iso",
    "legacy_mac",
    "legacy_regional",
    "dos",
    "mainframe",
    "all",
]

# Security: Maximum file size allowed for CLI detection (50 MB)
# Prevents memory exhaustion and DoS attacks via large files
_MAX_FILE_SIZE = 50 * 1024 * 1024


def _print_result(result: DetectionDict, label: str, *, minimal: bool) -> None:
    """Print a detection result to stdout."""
    if minimal:
        print(result["encoding"])
    else:
        print(f"{label}: {result['encoding']} with confidence {result['confidence']}")


def _validate_file_path(filepath: str) -> Path:
    """Validate file path for security.
    
    Security checks:
    - Resolves to an actual file (not directory)
    - Is not a symlink (prevents symlink attacks)
    - File size is within acceptable limits
    
    :param filepath: Path to validate
    :returns: Validated Path object
    :raises ValueError: If path fails security checks
    :raises OSError: If file access fails
    """
    path = Path(filepath)
    
    # Security: Check for symlinks before resolving
    if path.is_symlink():
        log_file_security(
            SecurityEventType.SYMLINK_BLOCKED,
            filepath,
            "Symlink detected and blocked",
        )
        raise ValueError("symlinks are not supported for security reasons")
    
    # Resolve to absolute path to prevent directory traversal
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        raise OSError(f"cannot access file: {e}") from e
    
    # Security: Ensure it's a regular file, not a directory or special file
    if not resolved.is_file():
        raise ValueError(f"not a regular file: {filepath}")
    
    # Security: Check file size before opening
    try:
        file_size = resolved.stat().st_size
        if file_size > _MAX_FILE_SIZE:
            log_file_security(
                SecurityEventType.FILE_SIZE_EXCEEDED,
                str(resolved),
                f"File size {file_size} exceeds maximum {_MAX_FILE_SIZE}",
            )
            raise ValueError(
                f"file too large ({file_size} bytes, max: {_MAX_FILE_SIZE} bytes)"
            )
    except OSError as e:
        raise OSError(f"cannot stat file: {e}") from e
    
    return resolved


def main(argv: list[str] | None = None) -> None:
    """Run the ``chardetect`` command-line tool.

    :param argv: Command-line arguments.  Defaults to ``sys.argv[1:]``.
    """
    parser = argparse.ArgumentParser(description="Detect character encoding of files.")
    parser.add_argument("files", nargs="*", help="Files to detect encoding of")
    parser.add_argument(
        "--minimal", action="store_true", help="Output only the encoding name"
    )
    parser.add_argument(
        "-e",
        "--encoding-era",
        default=None,
        choices=_ERA_NAMES,
        help="Encoding era filter",
    )
    parser.add_argument(
        "--version", action="version", version=f"chardet {chardet.__version__}"
    )

    args = parser.parse_args(argv)

    era_map = {
        "MODERN_WEB": EncodingEra.MODERN_WEB,
        "LEGACY_ISO": EncodingEra.LEGACY_ISO,
        "LEGACY_MAC": EncodingEra.LEGACY_MAC,
        "LEGACY_REGIONAL": EncodingEra.LEGACY_REGIONAL,
        "DOS": EncodingEra.DOS,
        "MAINFRAME": EncodingEra.MAINFRAME,
        "ALL": EncodingEra.ALL,
    }
    era = (
        era_map.get(args.encoding_era.upper(), EncodingEra.ALL)
        if args.encoding_era
        else EncodingEra.ALL
    )

    if args.files:
        errors = 0
        for filepath in args.files:
            # Security: Validate file path before opening
            try:
                resolved_path = _validate_file_path(filepath)
            except (ValueError, OSError) as e:
                print(f"chardetect: {filepath}: {e}", file=sys.stderr)
                errors += 1
                continue
            
            try:
                with resolved_path.open("rb") as f:
                    data = f.read(DEFAULT_MAX_BYTES)
            except OSError as e:
                print(f"chardetect: {filepath}: {e}", file=sys.stderr)
                errors += 1
                continue
            try:
                result = chardet.detect(data, encoding_era=era)
            except (ValueError, UnicodeDecodeError) as e:
                # Specific exceptions for known error types
                # ValueError: invalid parameters
                # UnicodeDecodeError: encoding/decoding failures
                print(f"chardetect: {filepath}: detection failed: {e}", file=sys.stderr)
                errors += 1
                continue
            except ChardetError as e:
                # chardet-specific errors (DetectionError, InvalidInputError, etc.)
                print(f"chardetect: {filepath}: detection failed: {e}", file=sys.stderr)
                errors += 1
                continue
            except RuntimeError as e:
                # Unexpected runtime errors - sanitize message to avoid leaking internals
                print(
                    f"chardetect: {filepath}: detection failed: unexpected error",
                    file=sys.stderr,
                )
                errors += 1
                continue
            _print_result(result, filepath, minimal=args.minimal)
        if errors == len(args.files):
            sys.exit(1)
    else:
        data = sys.stdin.buffer.read(DEFAULT_MAX_BYTES)
        try:
            result = chardet.detect(data, encoding_era=era)
        except (ValueError, UnicodeDecodeError) as e:
            # Specific exceptions for known error types
            # ValueError: invalid parameters
            # UnicodeDecodeError: encoding/decoding failures
            print(f"chardetect: stdin: detection failed: {e}", file=sys.stderr)
            sys.exit(1)
        except ChardetError as e:
            # chardet-specific errors (DetectionError, InvalidInputError, etc.)
            print(f"chardetect: stdin: detection failed: {e}", file=sys.stderr)
            sys.exit(1)
        except RuntimeError as e:
            # Unexpected runtime errors - sanitize message to avoid leaking internals
            print(f"chardetect: stdin: detection failed: unexpected error", file=sys.stderr)
            sys.exit(1)
        _print_result(result, "stdin", minimal=args.minimal)


if __name__ == "__main__":  # pragma: no cover
    main()
