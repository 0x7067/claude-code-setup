"""Tests for export functionality."""

import json
import pytest
from pathlib import Path
from setup_claude_code import (
    export_settings,
    export_skills,
    export_plugins_state,
    ExportResult,
)


class TestExportSettings:
    """Tests for export_settings function."""

    def test_exports_installed_settings(self, tmp_path):
        """Should copy installed settings to project config."""
        installed_path = tmp_path / "installed" / "settings.json"
        project_path = tmp_path / "project" / "config" / "settings.json"

        installed_path.parent.mkdir(parents=True)
        installed_settings = {"key": "value", "nested": {"a": 1}}
        installed_path.write_text(json.dumps(installed_settings))

        success, backup = export_settings(installed_path, project_path)

        assert success
        assert project_path.exists()
        exported = json.loads(project_path.read_text())
        assert exported == installed_settings

    def test_creates_backup_of_existing(self, tmp_path):
        """Should create backup when project config exists."""
        installed_path = tmp_path / "installed.json"
        project_path = tmp_path / "project.json"

        installed_path.write_text('{"new": "value"}')
        project_path.write_text('{"old": "value"}')

        success, backup = export_settings(installed_path, project_path)

        assert success
        assert backup is not None
        assert backup.exists()
        assert "old" in backup.read_text()

    def test_dry_run_no_changes(self, tmp_path):
        """Dry run should not modify files."""
        installed_path = tmp_path / "installed.json"
        project_path = tmp_path / "project.json"

        installed_path.write_text('{"key": "value"}')

        success, backup = export_settings(installed_path, project_path, dry_run=True)

        assert success
        assert not project_path.exists()

    def test_missing_installed_returns_false(self, tmp_path):
        """Should return False when installed settings don't exist."""
        success, backup = export_settings(
            tmp_path / "nonexistent.json",
            tmp_path / "project.json",
        )
        assert not success

    def test_invalid_json_returns_false(self, tmp_path):
        """Should return False for invalid JSON."""
        installed_path = tmp_path / "installed.json"
        installed_path.write_text("not valid json")

        success, backup = export_settings(installed_path, tmp_path / "project.json")
        assert not success


class TestExportSkills:
    """Tests for export_skills function."""

    def test_exports_new_skills(self, tmp_path):
        """Should copy new skills from installed to project."""
        installed_dir = tmp_path / "installed_skills"
        project_dir = tmp_path / "project_skills"

        skill_dir = installed_dir / "new-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("# New Skill")
        project_dir.mkdir(parents=True)

        exported = export_skills(installed_dir, project_dir)

        assert "new-skill" in exported
        assert (project_dir / "new-skill" / "skill.md").exists()

    def test_skips_existing_skills(self, tmp_path):
        """Should not overwrite existing project skills."""
        installed_dir = tmp_path / "installed_skills"
        project_dir = tmp_path / "project_skills"

        for base in [installed_dir, project_dir]:
            skill_dir = base / "existing-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.md").write_text(f"Content in {base.name}")

        exported = export_skills(installed_dir, project_dir)

        assert "existing-skill" not in exported
        # Original content preserved
        assert "project_skills" in (project_dir / "existing-skill" / "skill.md").read_text()

    def test_dry_run_no_changes(self, tmp_path):
        """Dry run should not create files."""
        installed_dir = tmp_path / "installed_skills"
        project_dir = tmp_path / "project_skills"

        skill_dir = installed_dir / "new-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("# New")

        exported = export_skills(installed_dir, project_dir, dry_run=True)

        assert "new-skill" in exported
        assert not (project_dir / "new-skill").exists()

    def test_missing_installed_dir(self, tmp_path):
        """Should handle missing installed directory gracefully."""
        exported = export_skills(
            tmp_path / "nonexistent",
            tmp_path / "project",
        )
        assert exported == []


class TestExportPluginsState:
    """Tests for export_plugins_state function."""

    def test_updates_enabled_states(self, tmp_path):
        """Should update plugin enabled states from installed settings."""
        plugins_path = tmp_path / "plugins.json"
        plugins_path.write_text(json.dumps({
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "enabled": True},
                {"name": "plugin2", "marketplace": "mp2", "enabled": False},
            ]
        }))

        installed_settings = {
            "enabledPlugins": {
                "plugin1@mp1": False,
                "plugin2@mp2": True,
            }
        }

        success, backup = export_plugins_state(installed_settings, plugins_path)

        assert success
        updated = json.loads(plugins_path.read_text())
        plugins = {p["name"]: p for p in updated["plugins"]}
        assert plugins["plugin1"]["enabled"] is False
        assert plugins["plugin2"]["enabled"] is True

    def test_no_changes_when_states_match(self, tmp_path):
        """Should not create backup when no changes needed."""
        plugins_path = tmp_path / "plugins.json"
        plugins_path.write_text(json.dumps({
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "enabled": True},
            ]
        }))

        installed_settings = {
            "enabledPlugins": {
                "plugin1@mp1": True,
            }
        }

        success, backup = export_plugins_state(installed_settings, plugins_path)

        assert success
        assert backup is None  # No changes, no backup needed

    def test_dry_run_no_changes(self, tmp_path):
        """Dry run should not modify files."""
        plugins_path = tmp_path / "plugins.json"
        original = json.dumps({
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "enabled": True},
            ]
        })
        plugins_path.write_text(original)

        installed_settings = {
            "enabledPlugins": {"plugin1@mp1": False}
        }

        success, backup = export_plugins_state(
            installed_settings, plugins_path, dry_run=True
        )

        assert success
        assert plugins_path.read_text() == original

    def test_disables_plugin_missing_from_installed(self, tmp_path):
        """Should mark plugin as disabled when absent from enabledPlugins."""
        plugins_path = tmp_path / "plugins.json"
        plugins_path.write_text(json.dumps({
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "enabled": True},
                {"name": "plugin2", "marketplace": "mp2", "enabled": True},
            ]
        }))

        installed_settings = {
            "enabledPlugins": {
                "plugin1@mp1": True,
                # plugin2 is missing - should be marked as disabled
            }
        }

        success, backup = export_plugins_state(installed_settings, plugins_path)

        assert success
        assert backup is not None  # Changes made
        updated = json.loads(plugins_path.read_text())
        plugins = {p["name"]: p for p in updated["plugins"]}
        assert plugins["plugin1"]["enabled"] is True
        assert plugins["plugin2"]["enabled"] is False

    def test_preserves_already_disabled_plugins(self, tmp_path):
        """Should not update plugins already marked as disabled."""
        plugins_path = tmp_path / "plugins.json"
        plugins_path.write_text(json.dumps({
            "plugins": [
                {"name": "plugin1", "marketplace": "mp1", "enabled": False},
            ]
        }))

        installed_settings = {
            "enabledPlugins": {}  # Empty - plugin1 not present
        }

        success, backup = export_plugins_state(installed_settings, plugins_path)

        assert success
        assert backup is None  # No changes needed
        updated = json.loads(plugins_path.read_text())
        assert updated["plugins"][0]["enabled"] is False


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_success_when_exit_success(self):
        """to_dict should show success when exit_code is 0."""
        result = ExportResult(exit_code=0)
        assert result.to_dict()["success"] is True

    def test_failure_when_exit_nonzero(self):
        """to_dict should show failure when exit_code is non-zero."""
        result = ExportResult(exit_code=6)
        assert result.to_dict()["success"] is False

    def test_to_dict_includes_all_fields(self):
        """to_dict should include all fields."""
        result = ExportResult(
            settings_exported=True,
            skills_exported=["skill1", "skill2"],
            plugins_exported=True,
            backups=["/path/backup1"],
            exit_code=0,
        )
        d = result.to_dict()
        assert d["settings_exported"] is True
        assert d["skills_exported"] == ["skill1", "skill2"]
        assert d["plugins_exported"] is True
        assert d["backups"] == ["/path/backup1"]
