"""Shared pytest fixtures for setup-claude-code tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from rich.console import Console


@pytest.fixture
def mock_console():
    """Mock Rich Console to avoid output during tests."""
    console = Mock(spec=Console)
    console.print = Mock()
    console.status = MagicMock()  # Context manager
    return console


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    """Create temporary home directory, isolate file operations."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home


@pytest.fixture
def claude_dir(temp_home):
    """Create .claude directory structure."""
    claude = temp_home / ".claude"
    claude.mkdir()
    (claude / "plugins").mkdir()
    (claude / "skills").mkdir()
    return claude


@pytest.fixture
def settings_file(claude_dir):
    """Create empty settings.json."""
    settings = claude_dir / "settings.json"
    settings.write_text("{}")
    return settings


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess.run for command execution."""
    mock_run = Mock()
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables for testing."""
    for var in ["NO_COLOR", "CLAUDE_SETUP_NO_COLOR", "TERM", "CLAUDE_SETUP_QUIET"]:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def mock_which(monkeypatch):
    """Mock shutil.which to simulate claude CLI availability."""
    def _mock_which(cmd):
        if cmd == "claude":
            return "/usr/bin/claude"
        return None

    monkeypatch.setattr("shutil.which", _mock_which)
    return _mock_which
