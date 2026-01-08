"""Tests for skill file creation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Import functions from the main script
sys.path.insert(0, str(Path(__file__).parent.parent))
from setup_claude_code import setup_skills


class TestSetupSkills:
    """Test skill file creation."""

    def test_creates_skill_file(self, claude_dir, mock_console):
        """Should create skill file with correct content."""
        results = setup_skills(console=mock_console)

        skill_file = claude_dir / "skills" / "design-principles" / "skill.md"
        assert skill_file.exists()
        assert "design-principles" in results
        assert results["design-principles"] == "created"

        content = skill_file.read_text()
        assert "name: design-principles" in content
        assert "description:" in content

    def test_idempotent_skips_existing(self, claude_dir, mock_console):
        """Should skip if skill already exists."""
        skill_dir = claude_dir / "skills" / "design-principles"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "skill.md"
        skill_file.write_text("existing content")

        results = setup_skills(console=mock_console)

        assert "skipped" in results["design-principles"].lower()
        assert skill_file.read_text() == "existing content"

    def test_dry_run_no_creation(self, claude_dir, mock_console):
        """Dry run should not create files."""
        results = setup_skills(dry_run=True, console=mock_console)

        skill_file = claude_dir / "skills" / "design-principles" / "skill.md"
        assert not skill_file.exists()
        assert "would" in results["design-principles"].lower()

    def test_creates_parent_directories(self, claude_dir, mock_console):
        """Should create parent directories if they don't exist."""
        # Remove skills directory
        import shutil
        shutil.rmtree(claude_dir / "skills")

        results = setup_skills(console=mock_console)

        skill_file = claude_dir / "skills" / "design-principles" / "skill.md"
        assert skill_file.exists()
        assert skill_file.parent.exists()

    def test_quiet_mode(self, claude_dir):
        """Quiet mode should suppress output."""
        results = setup_skills(quiet=True, console=None)

        assert "design-principles" in results

    def test_verbose_mode(self, claude_dir, mock_console):
        """Verbose mode should work."""
        results = setup_skills(verbose=True, console=mock_console)

        assert "design-principles" in results

    def test_skill_content_complete(self, claude_dir, mock_console):
        """Skill file should contain complete content."""
        results = setup_skills(console=mock_console)

        skill_file = claude_dir / "skills" / "design-principles" / "skill.md"
        content = skill_file.read_text()

        # Check for key sections
        assert "Design Principles" in content
        assert "Design Direction" in content
        assert "Core Craft Principles" in content
        assert "4px Grid" in content or "grid" in content.lower()

    def test_returns_status_dict(self, claude_dir, mock_console):
        """Should return dictionary with skill status."""
        results = setup_skills(console=mock_console)

        assert isinstance(results, dict)
        assert "design-principles" in results
        assert isinstance(results["design-principles"], str)
