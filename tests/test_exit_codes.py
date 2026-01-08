"""Tests for exit code correctness."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import functions and constants from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import (
    EXIT_MISSING_PREREQ,
    EXIT_PLUGIN_FAILED,
    EXIT_SETTINGS_FAILED,
    EXIT_SUCCESS,
    main,
)


class TestExitCodes:
    """Test exit code correctness."""

    def test_success_exit_code(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Successful run should return EXIT_SUCCESS (0)."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS
        assert exit_code == 0

    def test_missing_prereq_exit_code(self, monkeypatch):
        """Missing prerequisite should return EXIT_MISSING_PREREQ (2)."""
        monkeypatch.setattr("shutil.which", lambda x: None)
        monkeypatch.setattr("sys.argv", ["setup.py"])

        exit_code = main()

        assert exit_code == EXIT_MISSING_PREREQ
        assert exit_code == 2

    def test_plugin_failure_exit_code(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Plugin failure should set EXIT_PLUGIN_FAILED (3)."""
        # Make plugin installation fail
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Plugin installation failed"
        monkeypatch.setattr("sys.argv", ["setup.py"])

        exit_code = main()

        assert exit_code == EXIT_PLUGIN_FAILED
        assert exit_code == 3

    def test_dry_run_always_success(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Dry run should always return success."""
        # Even with failing mock, dry run should succeed
        mock_subprocess.return_value.returncode = 1
        monkeypatch.setattr("sys.argv", ["setup.py", "--dry-run"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_skip_plugins_no_plugin_failure(self, temp_home, mock_which, monkeypatch):
        """Skipping plugins should not trigger plugin failure exit code."""
        monkeypatch.setattr("sys.argv", ["setup.py", "--skip-plugins"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_exit_code_constants(self):
        """Verify exit code constants have correct values."""
        assert EXIT_SUCCESS == 0
        assert EXIT_MISSING_PREREQ == 2
        assert EXIT_PLUGIN_FAILED == 3
        assert EXIT_SETTINGS_FAILED == 5
