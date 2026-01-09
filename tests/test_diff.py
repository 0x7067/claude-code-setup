"""Tests for diff functionality."""

import pytest
from setup_claude_code import diff_settings, diff_skills, DiffResult


class TestDiffSettings:
    """Tests for diff_settings function."""

    def test_identical_configs_no_drift(self):
        """Identical configs should have no drift."""
        config = {"key1": "value1", "key2": "value2"}
        result = diff_settings(config, config.copy())
        assert not result.has_drift
        assert result.added == []
        assert result.removed == []
        assert result.modified == []
        assert set(result.unchanged) == {"settings.key1", "settings.key2"}

    def test_added_key_detected(self):
        """Keys only in installed should be marked as added."""
        project = {"key1": "value1"}
        installed = {"key1": "value1", "key2": "value2"}
        result = diff_settings(project, installed)
        assert result.has_drift
        assert "settings.key2" in result.added
        assert "settings.key1" in result.unchanged

    def test_removed_key_detected(self):
        """Keys only in project should be marked as removed."""
        project = {"key1": "value1", "key2": "value2"}
        installed = {"key1": "value1"}
        result = diff_settings(project, installed)
        assert result.has_drift
        assert "settings.key2" in result.removed
        assert "settings.key1" in result.unchanged

    def test_modified_value_detected(self):
        """Different values should be marked as modified."""
        project = {"key1": "value1"}
        installed = {"key1": "different"}
        result = diff_settings(project, installed)
        assert result.has_drift
        assert "settings.key1" in result.modified

    def test_empty_configs(self):
        """Empty configs should have no drift."""
        result = diff_settings({}, {})
        assert not result.has_drift

    def test_complex_values_compared(self):
        """Complex nested values should be compared correctly."""
        project = {"nested": {"a": 1, "b": 2}}
        installed = {"nested": {"a": 1, "b": 3}}
        result = diff_settings(project, installed)
        assert result.has_drift
        assert "settings.nested" in result.modified


class TestDiffSkills:
    """Tests for diff_skills function."""

    def test_identical_skills_no_drift(self, tmp_path):
        """Identical skill directories should have no drift."""
        project_skills = tmp_path / "project_skills"
        installed_skills = tmp_path / "installed_skills"

        for base in [project_skills, installed_skills]:
            skill_dir = base / "my-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.md").write_text("# Skill content")

        result = diff_skills(project_skills, installed_skills)
        assert not result.has_drift
        assert "skill:my-skill" in result.unchanged

    def test_new_installed_skill_detected(self, tmp_path):
        """Skills only in installed should be marked as added."""
        project_skills = tmp_path / "project_skills"
        installed_skills = tmp_path / "installed_skills"

        project_skills.mkdir(parents=True)
        (installed_skills / "new-skill").mkdir(parents=True)
        (installed_skills / "new-skill" / "skill.md").write_text("# New")

        result = diff_skills(project_skills, installed_skills)
        assert result.has_drift
        assert "skill:new-skill" in result.added

    def test_removed_skill_detected(self, tmp_path):
        """Skills only in project should be marked as removed."""
        project_skills = tmp_path / "project_skills"
        installed_skills = tmp_path / "installed_skills"

        (project_skills / "old-skill").mkdir(parents=True)
        (project_skills / "old-skill" / "skill.md").write_text("# Old")
        installed_skills.mkdir(parents=True)

        result = diff_skills(project_skills, installed_skills)
        assert result.has_drift
        assert "skill:old-skill" in result.removed

    def test_modified_skill_detected(self, tmp_path):
        """Skills with different content should be marked as modified."""
        project_skills = tmp_path / "project_skills"
        installed_skills = tmp_path / "installed_skills"

        for base, content in [(project_skills, "v1"), (installed_skills, "v2")]:
            skill_dir = base / "changed-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "skill.md").write_text(content)

        result = diff_skills(project_skills, installed_skills)
        assert result.has_drift
        assert "skill:changed-skill" in result.modified

    def test_nonexistent_directories(self, tmp_path):
        """Non-existent directories should be handled gracefully."""
        result = diff_skills(
            tmp_path / "nonexistent1",
            tmp_path / "nonexistent2",
        )
        assert not result.has_drift


class TestDiffResult:
    """Tests for DiffResult dataclass."""

    def test_has_drift_with_added(self):
        """has_drift should be True when there are added items."""
        result = DiffResult(added=["item1"])
        assert result.has_drift

    def test_has_drift_with_removed(self):
        """has_drift should be True when there are removed items."""
        result = DiffResult(removed=["item1"])
        assert result.has_drift

    def test_has_drift_with_modified(self):
        """has_drift should be True when there are modified items."""
        result = DiffResult(modified=["item1"])
        assert result.has_drift

    def test_no_drift_with_only_unchanged(self):
        """has_drift should be False when only unchanged items exist."""
        result = DiffResult(unchanged=["item1", "item2"])
        assert not result.has_drift

    def test_to_dict(self):
        """to_dict should return correct structure."""
        result = DiffResult(
            added=["a"],
            removed=["r"],
            modified=["m"],
            unchanged=["u"],
        )
        d = result.to_dict()
        assert d["added"] == ["a"]
        assert d["removed"] == ["r"]
        assert d["modified"] == ["m"]
        assert d["unchanged"] == ["u"]
        assert d["has_drift"] is True
