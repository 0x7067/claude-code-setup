"""Integration tests for main() function."""

from __future__ import annotations

import json
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
    check_prerequisites,
    main,
)


class TestCheckPrerequisites:
    """Test prerequisite checking."""

    def test_claude_cli_found(self, mock_which, mock_console):
        """Should return True when claude CLI is found."""
        err_console = Mock()
        result = check_prerequisites(mock_console, err_console)
        assert result is True

    def test_claude_cli_not_found(self, monkeypatch, mock_console):
        """Should return False when claude CLI is not found."""
        monkeypatch.setattr("shutil.which", lambda x: None)
        err_console = Mock()

        result = check_prerequisites(mock_console, err_console)

        assert result is False
        err_console.print.assert_called()


class TestMain:
    """Integration tests for main() function."""

    def test_full_run_success(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Should complete full setup successfully."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_missing_prereq_exits(self, monkeypatch):
        """Should exit with MISSING_PREREQ if claude not found."""
        monkeypatch.setattr("shutil.which", lambda x: None)
        monkeypatch.setattr("sys.argv", ["setup.py"])

        exit_code = main()

        assert exit_code == EXIT_MISSING_PREREQ

    def test_dry_run_no_changes(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Dry run should not make changes."""
        monkeypatch.setattr("sys.argv", ["setup.py", "--dry-run"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS
        # Should not install plugins (marketplaces might be checked)
        # But no actual installs should happen

    def test_skip_plugins_flag(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Should respect --skip-plugins flag."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--skip-plugins"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_skip_skills_flag(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Should respect --skip-skills flag."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--skip-skills"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_skip_settings_flag(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Should respect --skip-settings flag."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--skip-settings"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_json_output_mode(self, mock_subprocess, temp_home, mock_which, monkeypatch, capsys):
        """Should output JSON in JSON mode."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--json"])

        exit_code = main()

        captured = capsys.readouterr()
        # Should output valid JSON
        try:
            result = json.loads(captured.out)
            assert "success" in result
            assert "exit_code" in result
            assert result["exit_code"] == EXIT_SUCCESS
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_quiet_mode(self, mock_subprocess, temp_home, mock_which, monkeypatch, capsys):
        """Quiet mode should suppress output."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--quiet"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        # Quiet mode should produce minimal output
        assert len(captured.out) < 1000  # Arbitrary small size

    def test_no_color_flag(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Should respect --no-color flag."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--no-color"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_verbose_flag(self, mock_subprocess, temp_home, mock_which, monkeypatch):
        """Should respect --verbose flag."""
        mock_subprocess.return_value.returncode = 0
        monkeypatch.setattr("sys.argv", ["setup.py", "--verbose"])

        exit_code = main()

        assert exit_code == EXIT_SUCCESS

    def test_version_flag(self, monkeypatch, capsys):
        """Should display version and exit."""
        monkeypatch.setattr("sys.argv", ["setup.py", "--version"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "1.0.0" in captured.out

    def test_help_flag(self, monkeypatch, capsys):
        """Should display help and exit."""
        monkeypatch.setattr("sys.argv", ["setup.py", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "help" in captured.out.lower()
