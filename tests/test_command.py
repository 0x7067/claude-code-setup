"""Tests for command execution functions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import install_marketplace, install_plugin, run_command


class TestRunCommand:
    """Test run_command() subprocess execution."""

    def test_successful_command(self, mock_subprocess, mock_console):
        """Should return True for successful command."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "success"

        success, output = run_command(["echo", "test"], console=mock_console)

        assert success
        assert "success" in output
        mock_subprocess.assert_called_once()

    def test_failed_command(self, mock_subprocess):
        """Should return False for failed command."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "error"

        success, output = run_command(["false"])

        assert not success
        assert "error" in output

    def test_timeout_handling(self, monkeypatch):
        """Should handle timeout gracefully."""

        def timeout_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("cmd", 120)

        monkeypatch.setattr("subprocess.run", timeout_run)

        success, output = run_command(["sleep", "1000"], timeout=1)

        assert not success
        assert "timed out" in output.lower()

    def test_dry_run_no_execution(self, mock_subprocess, mock_console):
        """Dry run should not execute command."""
        success, output = run_command(
            ["echo", "test"], dry_run=True, console=mock_console
        )

        assert success
        assert output == ""
        mock_subprocess.assert_not_called()

    def test_verbose_output(self, mock_subprocess, mock_console):
        """Verbose mode should print output."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "verbose output"

        success, output = run_command(
            ["echo", "test"], verbose=True, console=mock_console
        )

        assert success
        mock_console.print.assert_called()

    def test_capture_stdout_and_stderr(self, mock_subprocess):
        """Should capture both stdout and stderr."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "out"
        mock_subprocess.return_value.stderr = "err"

        success, output = run_command(["test"])

        assert success
        assert "out" in output
        assert "err" in output

    def test_command_with_arguments(self, mock_subprocess):
        """Should pass all command arguments correctly."""
        mock_subprocess.return_value.returncode = 0

        run_command(["git", "status", "--short"])

        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert args == ["git", "status", "--short"]

    def test_custom_timeout(self, mock_subprocess):
        """Should use custom timeout value."""
        mock_subprocess.return_value.returncode = 0

        run_command(["test"], timeout=300)

        mock_subprocess.assert_called_once()
        kwargs = mock_subprocess.call_args[1]
        assert kwargs["timeout"] == 300

    def test_exception_handling(self, monkeypatch):
        """Should handle general exceptions."""

        def error_run(*args, **kwargs):
            raise Exception("Unexpected error")

        monkeypatch.setattr("subprocess.run", error_run)

        success, output = run_command(["test"])

        assert not success
        assert "Unexpected error" in output


class TestInstallMarketplace:
    """Test marketplace installation."""

    def test_install_new_marketplace(self, mock_subprocess, mock_console):
        """Should install new marketplace successfully."""
        mock_subprocess.return_value.returncode = 0

        success = install_marketplace(
            "github/org/repo", console=mock_console
        )

        assert success
        mock_subprocess.assert_called()
        args = mock_subprocess.call_args[0][0]
        assert "claude" in args
        assert "plugin" in args
        assert "marketplace" in args
        assert "add" in args
        assert "github/org/repo" in args

    def test_already_exists_succeeds(self, mock_subprocess, mock_console):
        """Should succeed if marketplace already exists."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = "already exists"

        success = install_marketplace(
            "github/org/repo", console=mock_console
        )

        assert success

    def test_dry_run(self, mock_subprocess, mock_console):
        """Dry run should not execute."""
        success = install_marketplace(
            "github/org/repo", dry_run=True, console=mock_console
        )

        assert success
        mock_subprocess.assert_not_called()


class TestInstallPlugin:
    """Test plugin installation."""

    def test_install_new_plugin(self, mock_subprocess, mock_console):
        """Should install new plugin successfully."""
        mock_subprocess.return_value.returncode = 0

        success, output = install_plugin(
            "claude-mem", "thedotmack", console=mock_console
        )

        assert success
        mock_subprocess.assert_called()
        args = mock_subprocess.call_args[0][0]
        assert args == ["claude", "plugin", "install", "claude-mem@thedotmack"]

    def test_plugin_install_failure(self, mock_subprocess, mock_console):
        """Should handle plugin installation failure."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Plugin not found"

        success, output = install_plugin(
            "nonexistent", "invalid", console=mock_console
        )

        assert not success

    def test_dry_run(self, mock_subprocess, mock_console):
        """Dry run should not execute."""
        success, output = install_plugin(
            "test", "marketplace", dry_run=True, console=mock_console
        )

        assert success
        mock_subprocess.assert_not_called()
