"""Tests for settings merge and configuration logic."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import merge_settings, setup_settings


class TestMergeSettings:
    """Test merge_settings() - most critical function."""

    def test_empty_existing_uses_template(self):
        """Empty existing dict should use template values."""
        existing = {}
        template = {"model": "sonnet", "alwaysThinkingEnabled": True}
        result = merge_settings(existing, template)
        assert result == template

    def test_direct_override_model(self):
        """model key should be overridden by template."""
        existing = {"model": "opus"}
        template = {"model": "sonnet"}
        result = merge_settings(existing, template)
        assert result["model"] == "sonnet"

    def test_direct_override_always_thinking(self):
        """alwaysThinkingEnabled should be overridden by template."""
        existing = {"alwaysThinkingEnabled": False}
        template = {"alwaysThinkingEnabled": True}
        result = merge_settings(existing, template)
        assert result["alwaysThinkingEnabled"] is True

    def test_direct_override_hooks(self):
        """hooks should be completely overridden by template."""
        existing = {"hooks": {"old": "hook"}}
        template = {"hooks": {"new": "hook"}}
        result = merge_settings(existing, template)
        assert result["hooks"] == {"new": "hook"}

    def test_direct_override_statusline(self):
        """statusLine should be completely overridden by template."""
        existing = {"statusLine": {"type": "old"}}
        template = {"statusLine": {"type": "new"}}
        result = merge_settings(existing, template)
        assert result["statusLine"] == {"type": "new"}

    def test_direct_override_enabled_plugins(self):
        """enabledPlugins should be completely overridden by template."""
        existing = {"enabledPlugins": {"old-plugin": True}}
        template = {"enabledPlugins": {"new-plugin": True}}
        result = merge_settings(existing, template)
        assert result["enabledPlugins"] == {"new-plugin": True}

    def test_env_merge_template_priority(self):
        """env dict should merge with template taking priority."""
        existing = {
            "env": {
                "EXISTING_VAR": "keep",
                "SHARED_VAR": "old_value",
            }
        }
        template = {
            "env": {
                "SHARED_VAR": "new_value",
                "NEW_VAR": "added",
            }
        }
        result = merge_settings(existing, template)

        assert result["env"]["EXISTING_VAR"] == "keep"
        assert result["env"]["SHARED_VAR"] == "new_value"  # Template wins
        assert result["env"]["NEW_VAR"] == "added"

    def test_env_missing_in_existing(self):
        """Handle missing env in existing."""
        existing = {}
        template = {"env": {"NEW_VAR": "value"}}
        result = merge_settings(existing, template)

        assert result["env"] == {"NEW_VAR": "value"}

    def test_permissions_union_sorted(self):
        """permissions should union allow/deny lists and sort."""
        existing = {
            "permissions": {
                "allow": ["Bash(git status)", "Bash(npm install)"],
                "deny": ["Read(.env)"],
            }
        }
        template = {
            "permissions": {
                "allow": ["Bash(npm install)", "Bash(docker:*)"],
                "deny": ["Read(.ssh/*)", "Read(.env)"],
            }
        }
        result = merge_settings(existing, template)

        # Should be union, deduplicated, sorted
        expected_allow = sorted([
            "Bash(git status)",
            "Bash(npm install)",
            "Bash(docker:*)",
        ])
        expected_deny = sorted([
            "Read(.env)",
            "Read(.ssh/*)",
        ])

        assert result["permissions"]["allow"] == expected_allow
        assert result["permissions"]["deny"] == expected_deny

    def test_permissions_preserves_ask(self):
        """permissions should preserve 'ask' key from existing."""
        existing = {
            "permissions": {
                "allow": ["Bash(ls)"],
                "ask": ["Write(*.py)"],
            }
        }
        template = {
            "permissions": {
                "allow": ["Bash(git status)"],
                "deny": ["Read(.env)"],
            }
        }
        result = merge_settings(existing, template)

        assert "ask" in result["permissions"]
        assert result["permissions"]["ask"] == ["Write(*.py)"]

    def test_unknown_keys_preserved(self):
        """Unknown keys in existing should be preserved."""
        existing = {
            "customKey": "custom_value",
            "anotherKey": {"nested": "data"},
        }
        template = {"model": "sonnet"}
        result = merge_settings(existing, template)

        assert result["customKey"] == "custom_value"
        assert result["anotherKey"] == {"nested": "data"}
        assert result["model"] == "sonnet"

    def test_empty_permissions_handling(self):
        """Handle empty permissions gracefully."""
        existing = {"permissions": {}}
        template = {
            "permissions": {
                "allow": ["Bash(ls)"],
                "deny": ["Read(.env)"],
            }
        }
        result = merge_settings(existing, template)

        assert result["permissions"]["allow"] == ["Bash(ls)"]
        assert result["permissions"]["deny"] == ["Read(.env)"]

    def test_missing_permissions_in_existing(self):
        """Handle missing permissions in existing."""
        existing = {}
        template = {
            "permissions": {
                "allow": ["Bash(ls)"],
                "deny": ["Read(.env)"],
            }
        }
        result = merge_settings(existing, template)

        assert result["permissions"]["allow"] == ["Bash(ls)"]
        assert result["permissions"]["deny"] == ["Read(.env)"]

    def test_all_overrides_together(self):
        """Test all direct overrides work together."""
        existing = {
            "model": "opus",
            "alwaysThinkingEnabled": False,
            "hooks": {"old": "hook"},
            "statusLine": {"type": "old"},
            "enabledPlugins": {"old": True},
            "customKey": "preserved",
        }
        template = {
            "model": "sonnet",
            "alwaysThinkingEnabled": True,
            "hooks": {"new": "hook"},
            "statusLine": {"type": "new"},
            "enabledPlugins": {"new": True},
        }
        result = merge_settings(existing, template)

        # All should be overridden with template values
        assert result["model"] == "sonnet"
        assert result["alwaysThinkingEnabled"] is True
        assert result["hooks"] == {"new": "hook"}
        assert result["statusLine"] == {"type": "new"}
        assert result["enabledPlugins"] == {"new": True}
        # Custom key should be preserved
        assert result["customKey"] == "preserved"


class TestSetupSettings:
    """Test setup_settings() - atomic writes with rollback."""

    def test_atomic_write_creates_new_file(self, tmp_path, mock_console):
        """Should create new settings file atomically."""
        settings_path = tmp_path / "settings.json"
        template = {"model": "sonnet"}

        success, status, backup = setup_settings(
            template, settings_path, console=mock_console
        )

        assert success
        assert status == "configured"
        assert settings_path.exists()

        content = json.loads(settings_path.read_text())
        assert content["model"] == "sonnet"

    def test_backup_created_before_update(self, tmp_path, mock_console):
        """Should create backup before updating existing file."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"old": "data"}')

        template = {"model": "sonnet"}
        success, status, backup = setup_settings(
            template, settings_path, console=mock_console
        )

        assert success
        assert backup is not None
        assert backup.exists()
        assert json.loads(backup.read_text())["old"] == "data"

    def test_merges_with_existing(self, tmp_path, mock_console):
        """Should merge template with existing settings."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text('{"customKey": "preserved", "model": "opus"}')

        template = {"model": "sonnet", "alwaysThinkingEnabled": True}
        success, status, backup = setup_settings(
            template, settings_path, console=mock_console
        )

        assert success
        content = json.loads(settings_path.read_text())
        assert content["model"] == "sonnet"  # Template wins
        assert content["customKey"] == "preserved"  # Existing preserved
        assert content["alwaysThinkingEnabled"] is True

    def test_invalid_json_in_existing(self, tmp_path, mock_console):
        """Should handle invalid JSON in existing file."""
        settings_path = tmp_path / "settings.json"
        settings_path.write_text("invalid json {")

        template = {"model": "sonnet"}
        success, status, backup = setup_settings(
            template, settings_path, console=mock_console
        )

        assert not success
        assert "invalid JSON" in status.lower() or "json" in status.lower()

    def test_dry_run_no_changes(self, tmp_path, mock_console):
        """Dry run should not make any changes."""
        settings_path = tmp_path / "settings.json"
        template = {"model": "sonnet"}

        success, status, backup = setup_settings(
            template, settings_path, dry_run=True, console=mock_console
        )

        assert success
        assert "would" in status.lower()
        assert not settings_path.exists()
        assert backup is None

    def test_creates_parent_directory(self, tmp_path, mock_console):
        """Should create parent directories if they don't exist."""
        settings_path = tmp_path / "subdir" / "settings.json"
        template = {"model": "sonnet"}

        success, status, backup = setup_settings(
            template, settings_path, console=mock_console
        )

        assert success
        assert settings_path.exists()
        assert settings_path.parent.exists()

    def test_trailing_newline_added(self, tmp_path, mock_console):
        """Should add trailing newline to JSON file."""
        settings_path = tmp_path / "settings.json"
        template = {"model": "sonnet"}

        success, status, backup = setup_settings(
            template, settings_path, console=mock_console
        )

        assert success
        content = settings_path.read_text()
        assert content.endswith("\n")
