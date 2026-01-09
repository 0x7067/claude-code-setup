"""Tests for external config loading functions."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
import setup_claude_code
from setup_claude_code import (
    load_settings_template,
    load_plugins_config,
    load_enabled_plugins,
    SETTINGS_TEMPLATE,
    PLUGINS,
    CONFIG_DIR,
)


class TestLoadSettingsTemplate:
    """Tests for load_settings_template function."""

    def test_loads_from_external_file(self, tmp_path):
        """Should load settings from external config file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        settings_path = config_dir / "settings.json"
        external_settings = {"custom": "value", "nested": {"key": 1}}
        settings_path.write_text(json.dumps(external_settings))

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_settings_template()

        assert result == external_settings

    def test_falls_back_to_embedded(self, tmp_path):
        """Should fall back to embedded template when file doesn't exist."""
        config_dir = tmp_path / "nonexistent"

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_settings_template()

        assert result == SETTINGS_TEMPLATE

    def test_falls_back_on_invalid_json(self, tmp_path):
        """Should fall back to embedded template on invalid JSON."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        settings_path = config_dir / "settings.json"
        settings_path.write_text("not valid json")

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_settings_template()

        assert result == SETTINGS_TEMPLATE


class TestLoadPluginsConfig:
    """Tests for load_plugins_config function."""

    def test_loads_from_external_file(self, tmp_path):
        """Should load plugins from external config file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        plugins_path = config_dir / "plugins.json"
        plugins_data = {
            "plugins": [
                {"name": "test-plugin", "marketplace": "test-mp", "repo": "test/repo"},
            ]
        }
        plugins_path.write_text(json.dumps(plugins_data))

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_plugins_config()

        assert result == [("test-plugin", "test-mp", "test/repo")]

    def test_falls_back_to_embedded(self, tmp_path):
        """Should fall back to embedded plugins when file doesn't exist."""
        config_dir = tmp_path / "nonexistent"

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_plugins_config()

        assert result == PLUGINS

    def test_falls_back_on_invalid_json(self, tmp_path):
        """Should fall back to embedded plugins on invalid JSON."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        plugins_path = config_dir / "plugins.json"
        plugins_path.write_text("invalid json")

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_plugins_config()

        assert result == PLUGINS


class TestLoadEnabledPlugins:
    """Tests for load_enabled_plugins function."""

    def test_loads_enabled_states(self, tmp_path):
        """Should load enabled states from external config."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        plugins_path = config_dir / "plugins.json"
        plugins_data = {
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "repo": "r1", "enabled": True},
                {"name": "plugin2", "marketplace": "mp2", "repo": "r2", "enabled": False},
            ]
        }
        plugins_path.write_text(json.dumps(plugins_data))

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_enabled_plugins()

        assert result == {
            "plugin1@mp1": True,
            "plugin2@mp2": False,
        }

    def test_returns_empty_when_no_file(self, tmp_path):
        """Should return empty dict when config file doesn't exist."""
        config_dir = tmp_path / "nonexistent"

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_enabled_plugins()

        assert result == {}

    def test_defaults_to_true_when_enabled_missing(self, tmp_path):
        """Should default to True when enabled key is missing."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        plugins_path = config_dir / "plugins.json"
        plugins_data = {
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "repo": "r1"},
            ]
        }
        plugins_path.write_text(json.dumps(plugins_data))

        with patch.object(setup_claude_code, 'CONFIG_DIR', config_dir):
            result = load_enabled_plugins()

        assert result == {"plugin1@mp1": True}
