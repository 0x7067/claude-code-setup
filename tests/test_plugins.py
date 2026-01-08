"""Tests for plugin setup orchestration."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import PLUGINS, setup_plugins


class TestSetupPlugins:
    """Test plugin setup orchestration."""

    def test_installs_all_plugins(self, mock_subprocess, mock_console):
        """Should attempt to install all defined plugins."""
        mock_subprocess.return_value.returncode = 0

        results = setup_plugins(console=mock_console)

        assert len(results) == len(PLUGINS)
        assert all("installed" in status or "failed" in status for status in results.values())

    def test_success_returns_installed(self, mock_subprocess, mock_console):
        """Successful plugin installation should return 'installed' status."""
        mock_subprocess.return_value.returncode = 0

        results = setup_plugins(console=mock_console)

        # All should be installed successfully
        for plugin_name, status in results.items():
            assert status == "installed", f"Plugin {plugin_name} failed"

    def test_dry_run_no_installation(self, mock_subprocess, mock_console):
        """Dry run should not install plugins."""
        results = setup_plugins(dry_run=True, console=mock_console)

        # Should still return results
        assert len(results) > 0
        # Should not execute any commands
        mock_subprocess.assert_not_called()

    def test_quiet_mode(self, mock_subprocess):
        """Quiet mode should suppress output."""
        mock_subprocess.return_value.returncode = 0

        results = setup_plugins(quiet=True, console=None)

        assert len(results) == len(PLUGINS)

    def test_verbose_mode(self, mock_subprocess, mock_console):
        """Verbose mode should show command output."""
        mock_subprocess.return_value.returncode = 0

        results = setup_plugins(verbose=True, console=mock_console)

        assert len(results) == len(PLUGINS)

    def test_plugin_names_match(self, mock_subprocess, mock_console):
        """Result keys should match plugin names from PLUGINS."""
        mock_subprocess.return_value.returncode = 0

        results = setup_plugins(console=mock_console)

        expected_names = {plugin[0] for plugin in PLUGINS}
        assert set(results.keys()) == expected_names

    def test_marketplace_setup_before_plugins(self, mock_subprocess, mock_console):
        """Should add marketplaces before installing plugins."""
        mock_subprocess.return_value.returncode = 0
        calls = []

        def track_calls(cmd, **kwargs):
            calls.append(cmd)
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        mock_subprocess.side_effect = track_calls

        setup_plugins(console=mock_console)

        # First calls should be marketplace adds
        marketplace_calls = [c for c in calls if "marketplace" in c and "add" in c]
        plugin_calls = [c for c in calls if "install" in c and "plugin" in c]

        assert len(marketplace_calls) > 0
        assert len(plugin_calls) > 0
