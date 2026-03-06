"""Command-line interface for chardet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chardet
from chardet._utils import DEFAULT_MAX_BYTES
from chardet.enums import EncodingEra
from chardet.pipeline import DetectionDict

# Hardcoded list since Rust enum doesn't support Python enum iteration
_ERA_NAMES = ["modern_web", "legacy_iso", "legacy_mac", "legacy_regional", "dos", "mainframe", "all"]


def _print_result(result: DetectionDict, label: str, *, minimal: bool) -> None:
    """Print a detection result to stdout."""
    if minimal:
        print(result["encoding"])
    else:
        print(f"{label}: {result['encoding']} with confidence {result['confidence']}")


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
    era = era_map.get(args.encoding_era.upper(), EncodingEra.ALL) if args.encoding_era else EncodingEra.ALL

    if args.files:
        errors = 0
        for filepath in args.files:
            try:
                with Path(filepath).open("rb") as f:
                    data = f.read(DEFAULT_MAX_BYTES)
            except OSError as e:
                print(f"chardetect: {filepath}: {e}", file=sys.stderr)
                errors += 1
                continue
            try:
                result = chardet.detect(data, encoding_era=era)
            except Exception as e:  # noqa: BLE001
                print(f"chardetect: {filepath}: detection failed: {e}", file=sys.stderr)
                errors += 1
                continue
            _print_result(result, filepath, minimal=args.minimal)
        if errors == len(args.files):
            sys.exit(1)
    else:
        data = sys.stdin.buffer.read(DEFAULT_MAX_BYTES)
        try:
            result = chardet.detect(data, encoding_era=era)
        except Exception as e:  # noqa: BLE001
            print(f"chardetect: stdin: detection failed: {e}", file=sys.stderr)
            sys.exit(1)
        _print_result(result, "stdin", minimal=args.minimal)


if __name__ == "__main__":  # pragma: no cover
    main()
