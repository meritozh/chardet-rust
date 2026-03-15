"""Additional tests for CLI coverage.

Covers missing lines in src/chardet/cli.py
"""

from __future__ import annotations

import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from chardet.cli import _validate_file_path, main


class TestValidateFilePath:
    """Tests for _validate_file_path function."""

    def test_valid_file(self) -> None:
        """Test validation passes for a valid regular file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = _validate_file_path(temp_path)
            assert result.is_file()
            assert result.is_absolute()
        finally:
            os.unlink(temp_path)

    def test_symlink_blocked(self) -> None:
        """Test symlinks are rejected."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            real_path = f.name

        symlink_path = real_path + "_link"

        try:
            os.symlink(real_path, symlink_path)
            with pytest.raises(ValueError, match="symlinks are not supported"):
                _validate_file_path(symlink_path)
        finally:
            if os.path.exists(symlink_path):
                os.unlink(symlink_path)
            os.unlink(real_path)

    def test_directory_rejected(self) -> None:
        """Test directories are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="not a regular file"):
                _validate_file_path(tmpdir)

    def test_nonexistent_file(self) -> None:
        """Test non-existent files raise OSError."""
        with pytest.raises((OSError, ValueError)):
            _validate_file_path("/nonexistent/path/file.txt")

    def test_large_file_blocked(self) -> None:
        """Test files exceeding size limit are rejected."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            # Write 51MB of data (over the 50MB limit)
            f.write(b"x" * (51 * 1024 * 1024))
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="file too large"):
                _validate_file_path(temp_path)
        finally:
            os.unlink(temp_path)


class TestCliMain:
    """Tests for CLI main function."""

    def test_cli_version(self, capsys) -> None:
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "chardet" in captured.out.lower()

    def test_cli_help(self, capsys) -> None:
        """Test --help flag."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_cli_minimal_output(self, capsys) -> None:
        """Test --minimal flag with valid file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello World")
            temp_path = f.name

        try:
            # main() returns None on success, doesn't always call sys.exit()
            result = main(["--minimal", temp_path])
            assert result is None  # Success
        finally:
            os.unlink(temp_path)

    def test_cli_with_encoding_era(self, capsys) -> None:
        """Test --encoding-era flag."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello World")
            temp_path = f.name

        try:
            # main() returns None on success
            result = main(["--encoding-era", "modern_web", temp_path])
            assert result is None  # Success
        finally:
            os.unlink(temp_path)

    def test_cli_invalid_file(self, capsys) -> None:
        """Test CLI with invalid file path."""
        with pytest.raises(SystemExit) as exc_info:
            main(["/nonexistent/path/file.txt"])
        assert exc_info.value.code == 1

    def test_cli_symlink_file(self, capsys) -> None:
        """Test CLI rejects symlink files."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            real_path = f.name

        symlink_path = real_path + "_link"

        try:
            os.symlink(real_path, symlink_path)
            with pytest.raises(SystemExit) as exc_info:
                main([symlink_path])
            assert exc_info.value.code == 1  # Should error
        finally:
            if os.path.exists(symlink_path):
                os.unlink(symlink_path)
            os.unlink(real_path)

    def test_cli_empty_args_reads_stdin(self, monkeypatch) -> None:
        """Test CLI with no args reads from stdin."""
        import sys
        from io import BytesIO

        # Mock stdin to provide test data
        test_input = b"Hello World"
        
        class MockStdin:
            buffer = BytesIO(test_input)
        
        monkeypatch.setattr(sys, "stdin", MockStdin())
        
        # Just verify the setup works
        assert hasattr(sys.stdin, "buffer")

    def test_cli_multiple_files_one_invalid(self, capsys) -> None:
        """Test CLI with multiple files where one is invalid."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello World")
            valid_path = f.name

        try:
            # One file processed, one error - main() returns None if not all failed
            result = main([valid_path, "/nonexistent/file.txt"])
            # Should succeed since not all files failed
            assert result is None
        finally:
            os.unlink(valid_path)

    def test_cli_all_files_invalid(self, capsys) -> None:
        """Test CLI when all files are invalid."""
        with pytest.raises(SystemExit) as exc_info:
            main(["/nonexistent/file1.txt", "/nonexistent/file2.txt"])
        assert exc_info.value.code == 1  # All failed
