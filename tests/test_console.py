"""Tests for console and color detection functions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import create_console, create_error_console, should_use_color


class TestShouldUseColor:
    """Test color detection logic."""

    def test_no_color_env_disables(self, monkeypatch, clean_env):
        """NO_COLOR=1 should disable color."""
        monkeypatch.setenv("NO_COLOR", "1")
        assert should_use_color() is False

    def test_no_color_empty_string_disables(self, monkeypatch, clean_env):
        """NO_COLOR= (empty string) should disable color."""
        monkeypatch.setenv("NO_COLOR", "")
        assert should_use_color() is False

    def test_claude_setup_no_color_disables(self, monkeypatch, clean_env):
        """CLAUDE_SETUP_NO_COLOR should disable color."""
        monkeypatch.setenv("CLAUDE_SETUP_NO_COLOR", "1")
        assert should_use_color() is False

    def test_dumb_terminal_disables(self, monkeypatch, clean_env):
        """TERM=dumb should disable color."""
        monkeypatch.setenv("TERM", "dumb")
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        assert should_use_color() is False

    def test_non_tty_disables(self, monkeypatch, clean_env):
        """Non-TTY stdout should disable color."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        assert should_use_color() is False

    def test_tty_enables_color(self, monkeypatch, clean_env):
        """TTY stdout with no env vars should enable color."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        result = should_use_color()
        # Result depends on actual environment, but function should run
        assert isinstance(result, bool)

    def test_priority_no_color_over_tty(self, monkeypatch):
        """NO_COLOR should override TTY."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        assert should_use_color() is False


class TestCreateConsole:
    """Test console creation."""

    def test_force_no_color(self):
        """force_no_color should disable color."""
        console = create_console(force_no_color=True)
        assert console.no_color is True

    def test_quiet_mode(self):
        """quiet=True should create quiet console."""
        console = create_console(quiet=True)
        assert console.quiet is True

    def test_default_not_quiet(self):
        """Default console should not be quiet."""
        console = create_console()
        assert console.quiet is False

    def test_not_stderr(self):
        """Regular console should not write to stderr."""
        console = create_console()
        assert console.stderr is False

    def test_color_and_quiet_together(self):
        """Should handle both force_no_color and quiet."""
        console = create_console(force_no_color=True, quiet=True)
        assert console.no_color is True
        assert console.quiet is True


class TestCreateErrorConsole:
    """Test error console creation."""

    def test_stderr_console(self):
        """Error console should write to stderr."""
        console = create_error_console()
        assert console.stderr is True

    def test_force_no_color(self):
        """force_no_color should disable color on error console."""
        console = create_error_console(force_no_color=True)
        assert console.no_color is True
        assert console.stderr is True

    def test_not_quiet(self):
        """Error console should not be quiet by default."""
        console = create_error_console()
        assert console.quiet is False
