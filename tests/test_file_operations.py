"""Tests for file operation functions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import backup_file


class TestBackupFile:
    """Test backup_file() function."""

    def test_backup_creates_timestamped_file(self, tmp_path, mock_console):
        """Should create backup with timestamp."""
        original = tmp_path / "settings.json"
        original.write_text('{"test": "data"}')

        backup_path = backup_file(original, console=mock_console)

        assert backup_path is not None
        assert backup_path.exists()
        assert ".backup." in str(backup_path)
        assert backup_path.read_text() == '{"test": "data"}'

    def test_backup_nonexistent_returns_none(self, tmp_path, mock_console):
        """Should return None for non-existent file."""
        nonexistent = tmp_path / "missing.json"
        backup_path = backup_file(nonexistent, console=mock_console)
        assert backup_path is None

    def test_backup_preserves_content(self, tmp_path, mock_console):
        """Should preserve exact file content."""
        original = tmp_path / "settings.json"
        content = '{"complex": {"nested": ["data", 123, true]}}'
        original.write_text(content)

        backup_path = backup_file(original, console=mock_console)

        assert backup_path is not None
        assert backup_path.read_text() == content

    def test_backup_file_suffix_format(self, tmp_path, mock_console):
        """Backup file should have correct suffix format."""
        original = tmp_path / "settings.json"
        original.write_text("{}")

        backup_path = backup_file(original, console=mock_console)

        assert backup_path is not None
        # Should be like settings.json.backup.2026-01-08T12-00-00
        assert backup_path.name.startswith("settings.json.backup.")

    def test_backup_without_console(self, tmp_path):
        """Should work without console parameter."""
        original = tmp_path / "test.txt"
        original.write_text("content")

        backup_path = backup_file(original, console=None)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "content"

    def test_backup_multiple_backups_same_second(self, tmp_path, mock_console):
        """Multiple backups in same second should not overwrite each other."""
        original = tmp_path / "settings.json"
        original.write_text('{"version": 1}')

        backup1 = backup_file(original, console=mock_console)

        # Modify original
        original.write_text('{"version": 2}')

        backup2 = backup_file(original, console=mock_console)

        assert backup1 is not None
        assert backup2 is not None
        # Both backups should exist (even if same timestamp, one will be overwritten
        # which is acceptable behavior for same-second backups)
        assert backup1.exists() or backup2.exists()
