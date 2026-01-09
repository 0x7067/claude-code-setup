#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=13.0.0"]
# ///
"""
Claude Code Setup Script

Replicates a curated Claude Code configuration including plugins and skills.
Run with: uv run ~/setup-claude-code.py

For issues: https://github.com/anthropics/claude-code/issues
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

__version__ = "1.0.0"

# Exit codes following CLI best practices
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_MISSING_PREREQ = 2
EXIT_PLUGIN_FAILED = 3
EXIT_SKILL_FAILED = 4
EXIT_SETTINGS_FAILED = 5
EXIT_EXPORT_FAILED = 6
EXIT_SYNC_FAILED = 7
EXIT_DRIFT_DETECTED = 8

# Global state for tracking partial completion on interrupt
_completed_steps: list[str] = []


def should_use_color() -> bool:
    """Check if we should use colored output."""
    # Respect NO_COLOR (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("CLAUDE_SETUP_NO_COLOR"):
        return False
    # Check if stdout is a TTY
    if not sys.stdout.isatty():
        return False
    # Check for dumb terminal
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def create_console(force_no_color: bool = False, quiet: bool = False) -> Console:
    """Create a Rich console with appropriate settings."""
    use_color = should_use_color() and not force_no_color
    return Console(
        force_terminal=use_color,
        no_color=not use_color,
        quiet=quiet,
        stderr=False,
    )


def create_error_console(force_no_color: bool = False) -> Console:
    """Create a Rich console for stderr."""
    use_color = should_use_color() and not force_no_color
    return Console(
        force_terminal=use_color,
        no_color=not use_color,
        stderr=True,
    )


# Plugin definitions: (plugin_name, marketplace, github_repo)
PLUGINS = [
    ("claude-mem", "thedotmack", "thedotmack/claude-mem"),
    ("plannotator", "plannotator", "backnotprop/plannotator"),
    ("ac-dev-tools", "alteredcraft-plugins", "AlteredCraft/claude-code-plugins"),
    ("ac-ideation", "alteredcraft-plugins", "AlteredCraft/claude-code-plugins"),
    ("claude-hud", "claude-hud", "jarrodwatts/claude-hud"),
    ("code-review", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("commit-commands", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("feature-dev", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("swift-lsp", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("mgrep", "Mixedbread-Grep", "mixedbread-ai/mgrep"),
]

# Directory containing skill files to install
SKILLS_DIR = Path(__file__).parent / "skills"

# Directory containing external config files
CONFIG_DIR = Path(__file__).parent / "config"


def load_settings_template() -> dict:
    """Load settings template from external config or fall back to embedded default."""
    config_path = CONFIG_DIR / "settings.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    # Fall back to embedded default
    return SETTINGS_TEMPLATE


def load_plugins_config() -> list[tuple[str, str, str]]:
    """Load plugins config from external file or fall back to embedded default.

    Returns list of (plugin_name, marketplace, repo) tuples.
    """
    config_path = CONFIG_DIR / "plugins.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return [
                    (p["name"], p["marketplace"], p["repo"])
                    for p in data.get("plugins", [])
                ]
        except (json.JSONDecodeError, IOError, KeyError):
            pass
    # Fall back to embedded default
    return PLUGINS


def load_enabled_plugins() -> dict[str, bool]:
    """Load enabled plugins state from external config."""
    config_path = CONFIG_DIR / "plugins.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return {
                    f"{p['name']}@{p['marketplace']}": p.get("enabled", True)
                    for p in data.get("plugins", [])
                }
        except (json.JSONDecodeError, IOError, KeyError):
            pass
    return {}

# Settings.json template with full configuration
SETTINGS_TEMPLATE = {
    "alwaysThinkingEnabled": True,
    "env": {
        "ENABLE_TOOL_SEARCH": "true",
        "DISABLE_AUTOUPDATER": "1"
    },
    "permissions": {
        "allow": [
            # npm/yarn/pnpm
            "Bash(npm install)",
            "Bash(npm run:*)",
            "Bash(npm test:*)",
            "Bash(npx:*)",
            "Bash(yarn:*)",
            "Bash(pnpm:*)",
            # git commands
            "Bash(git status)",
            "Bash(git diff:*)",
            "Bash(git log:*)",
            "Bash(git branch:*)",
            "Bash(git checkout:*)",
            "Bash(git add:*)",
            "Bash(git commit:*)",
            "Bash(git push:*)",
            "Bash(git pull:*)",
            "Bash(git fetch:*)",
            "Bash(git stash:*)",
            "Bash(git merge:*)",
            "Bash(git rebase:*)",
            # file operations
            "Bash(ls:*)",
            "Bash(cat:*)",
            "Bash(head:*)",
            "Bash(tail:*)",
            "Bash(grep:*)",
            "Bash(find:*)",
            "Bash(wc:*)",
            "Bash(pwd)",
            "Bash(which:*)",
            "Bash(echo:*)",
            # programming languages
            "Bash(node:*)",
            "Bash(python:*)",
            "Bash(python3:*)",
            "Bash(pip:*)",
            "Bash(pip3:*)",
            "Bash(cargo:*)",
            "Bash(go:*)",
            "Bash(make:*)",
            # docker
            "Bash(docker:*)",
            "Bash(docker-compose:*)",
            # swift/xcode
            "Bash(xcodebuild:*)",
            "Bash(xcrun:*)",
            "Bash(xcode-select:*)",
            "Bash(xcrun simctl:*)",
            "Bash(swift:*)",
            "Bash(swiftc:*)",
            "Bash(swift build:*)",
            "Bash(swift test:*)",
            "Bash(swift run:*)",
            "Bash(swift package:*)",
            "Bash(ibtool:*)",
            "Bash(actool:*)",
            "Bash(plutil:*)",
            "Bash(codesign:*)",
            "Bash(security:*)",
            "Bash(otool:*)",
            "Bash(lipo:*)",
            "Bash(dsymutil:*)"
        ],
        "deny": [
            "Read(.env)",
            "Read(.env.*)",
            "Read(.envrc)",
            "Read(./secrets/**)",
            "Read(~/.aws/**)",
            "Read(~/.ssh/**)",
            "Read(~/.kube/**)",
            "Read(~/.npmrc)",
            "Read(~/.netrc)"
        ]
    },
    "hooks": {
        "UserPromptSubmit": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "echo \"For context, today's date is $(date). Please use this as the current date for all time-relative questions.\""
                    }
                ]
            }
        ]
    },
    "statusLine": {
        "type": "command",
        "command": "bash -c '\"$(command -v bun || command -v node)\" \"$(ls -td ~/.claude/plugins/cache/claude-hud/claude-hud/*/ 2>/dev/null | head -1)src/index.ts\"'"
    },
    "enabledPlugins": {
        "claude-mem@thedotmack": False,
        "plannotator@plannotator": True,
        "ac-dev-tools@alteredcraft-plugins": True,
        "ac-ideation@alteredcraft-plugins": True,
        "code-review@claude-plugins-official": True,
        "commit-commands@claude-plugins-official": True,
        "feature-dev@claude-plugins-official": True,
        "swift-lsp@claude-plugins-official": True,
        "mgrep@Mixedbread-Grep": False,
        "claude-hud@claude-hud": True
    }
}



@dataclass
class SetupResult:
    """Result of the setup operation."""
    plugins: dict[str, str] = field(default_factory=dict)  # plugin -> status
    skills: dict[str, str] = field(default_factory=dict)   # skill -> status
    settings: dict[str, str] = field(default_factory=dict)  # settings file -> status
    backups: list[str] = field(default_factory=list)  # backup file paths
    exit_code: int = EXIT_SUCCESS

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "success": self.exit_code == EXIT_SUCCESS,
            "exit_code": self.exit_code,
            "plugins": self.plugins,
            "skills": self.skills,
            "settings": self.settings,
            "backups": self.backups,
        }


@dataclass
class DiffResult:
    """Result of comparing project config with installed config."""
    added: list[str] = field(default_factory=list)      # New in installed
    removed: list[str] = field(default_factory=list)    # Missing from installed
    modified: list[str] = field(default_factory=list)   # Different values
    unchanged: list[str] = field(default_factory=list)  # Same values

    @property
    def has_drift(self) -> bool:
        """Check if there are any differences."""
        return bool(self.added or self.removed or self.modified)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "unchanged": self.unchanged,
            "has_drift": self.has_drift,
        }


@dataclass
class ExportResult:
    """Result of export operation."""
    settings_exported: bool = False
    skills_exported: list[str] = field(default_factory=list)
    plugins_exported: bool = False
    backups: list[str] = field(default_factory=list)
    exit_code: int = EXIT_SUCCESS

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "success": self.exit_code == EXIT_SUCCESS,
            "exit_code": self.exit_code,
            "settings_exported": self.settings_exported,
            "skills_exported": self.skills_exported,
            "plugins_exported": self.plugins_exported,
            "backups": self.backups,
        }


def handle_interrupt(signum: int, frame) -> None:
    """Handle Ctrl-C gracefully."""
    err_console = create_error_console()
    err_console.print("\n[yellow]Interrupted.[/yellow]")
    if _completed_steps:
        err_console.print(f"[dim]Completed: {', '.join(_completed_steps)}[/dim]")
    err_console.print("[dim]You can safely re-run this script to continue.[/dim]")
    sys.exit(130)  # Standard exit code for SIGINT


def check_prerequisites(console: Console, err_console: Console) -> bool:
    """Check if claude CLI is installed."""
    if shutil.which("claude") is None:
        err_console.print(
            "[red]Error:[/red] Claude Code CLI not found.\n"
            "Install it from: https://docs.anthropic.com/en/docs/claude-code"
        )
        return False
    return True


def run_command(
    cmd: list[str],
    dry_run: bool = False,
    verbose: bool = False,
    console: Console | None = None,
    timeout: int = 120,
) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    if dry_run:
        if console:
            console.print(f"  [dim]Would run:[/dim] {' '.join(cmd)}")
        return True, ""

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        if verbose and console:
            if result.stdout.strip():
                console.print(f"  [dim]{result.stdout.strip()}[/dim]")
            if result.stderr.strip():
                console.print(f"  [yellow]{result.stderr.strip()}[/yellow]")
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def install_marketplace(
    repo: str,
    dry_run: bool = False,
    verbose: bool = False,
    console: Console | None = None,
) -> bool:
    """Add a plugin marketplace."""
    cmd = ["claude", "plugin", "marketplace", "add", repo]
    success, output = run_command(cmd, dry_run, verbose, console)
    # Marketplace might already exist, which is fine
    if not success and "already" not in output.lower():
        return False
    return True


def install_plugin(
    plugin: str,
    marketplace: str,
    dry_run: bool = False,
    verbose: bool = False,
    console: Console | None = None,
) -> tuple[bool, str]:
    """Install a plugin from a marketplace. Idempotent - succeeds if already installed."""
    cmd = ["claude", "plugin", "install", f"{plugin}@{marketplace}"]
    success, output = run_command(cmd, dry_run, verbose, console)
    return success, output


def setup_plugins(
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    console: Console | None = None,
) -> dict[str, str]:
    """Install all plugins. Returns dict of plugin name -> status.

    The CLI handles idempotency - installing an already-installed plugin
    succeeds and updates it to the latest version.
    """
    global _completed_steps
    results: dict[str, str] = {}

    # Load plugins from external config or fallback
    plugins = load_plugins_config()

    # Get unique marketplaces
    marketplaces = {}
    for plugin, marketplace, repo in plugins:
        if marketplace not in marketplaces:
            marketplaces[marketplace] = repo

    # Add marketplaces first
    if console and not quiet:
        console.print("\n[bold]Adding plugin marketplaces...[/bold]")

    for marketplace, repo in marketplaces.items():
        if console and not quiet:
            with console.status(f"Adding {marketplace}..."):
                success = install_marketplace(repo, dry_run, verbose, console if verbose else None)
                status = "[green]done[/green]" if success else "[red]failed[/red]"
                console.print(f"  {marketplace}: {status}")
        else:
            install_marketplace(repo, dry_run, verbose)

    # Install plugins
    if console and not quiet:
        console.print("\n[bold]Installing plugins...[/bold]")

    for plugin, marketplace, _ in plugins:
        if console and not quiet:
            with console.status(f"Installing {plugin}..."):
                success, _ = install_plugin(plugin, marketplace, dry_run, verbose, console if verbose else None)
                if success:
                    results[plugin] = "installed"
                    _completed_steps.append(f"plugin:{plugin}")
                    console.print(f"  {plugin}: [green]installed[/green]")
                else:
                    results[plugin] = "failed"
                    console.print(f"  {plugin}: [red]failed[/red]")
        else:
            success, _ = install_plugin(plugin, marketplace, dry_run, verbose)
            results[plugin] = "installed" if success else "failed"
            if success:
                _completed_steps.append(f"plugin:{plugin}")

    return results


def setup_skills(
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    console: Console | None = None,
) -> dict[str, str]:
    """Copy skill files from bundled skills directory. Returns dict of skill name -> status."""
    global _completed_steps
    results: dict[str, str] = {}

    if console and not quiet:
        console.print("\n[bold]Setting up skills...[/bold]")

    dest_skills_dir = Path.home() / ".claude" / "skills"

    # Check if source skills directory exists
    if not SKILLS_DIR.exists():
        if console and not quiet:
            console.print(f"  [red]Skills directory not found:[/red] {SKILLS_DIR}")
        results["skills"] = "failed: source directory not found"
        return results

    # Process each skill directory
    for skill_src in SKILLS_DIR.iterdir():
        if not skill_src.is_dir():
            continue

        skill_name = skill_src.name
        skill_dest = dest_skills_dir / skill_name

        # Check if already exists (idempotent)
        if skill_dest.exists() and not dry_run:
            results[skill_name] = "skipped (already exists)"
            if console and not quiet:
                console.print(f"  {skill_name}: [cyan]skipped[/cyan] (already exists)")
            continue

        if dry_run:
            if console and not quiet:
                console.print(f"  [dim]Would copy:[/dim] {skill_src} -> {skill_dest}")
            results[skill_name] = "would create"
            continue

        try:
            # Copy entire skill directory tree
            shutil.copytree(skill_src, skill_dest, dirs_exist_ok=True)
            results[skill_name] = "created"
            _completed_steps.append(f"skill:{skill_name}")
            if console and not quiet:
                console.print(f"  {skill_name}: [green]created[/green]")
        except Exception as e:
            results[skill_name] = f"failed: {e}"
            if console and not quiet:
                console.print(f"  {skill_name}: [red]failed[/red] - {e}")

    return results


def backup_file(file_path: Path, console: Console | None = None) -> Path | None:
    """Create timestamped backup of a file. Returns backup path or None if failed."""
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{timestamp}")

    try:
        shutil.copy2(file_path, backup_path)
        if console:
            console.print(f"  [dim]Backup created:[/dim] {backup_path}")
        return backup_path
    except Exception as e:
        if console:
            console.print(f"  [red]Backup failed:[/red] {e}")
        return None


def merge_settings(existing: dict, template: dict) -> dict:
    """Merge settings with template, using intelligent strategy.

    - Simple keys (alwaysThinkingEnabled): template overrides
    - env: merge with template priority
    - permissions: union of allow/deny lists
    - hooks, statusLine, enabledPlugins: template overrides
    - Unknown keys (including mcpServers): preserved from existing
    """
    result = existing.copy()

    # Direct overrides
    for key in ["alwaysThinkingEnabled", "hooks", "statusLine", "enabledPlugins"]:
        if key in template:
            result[key] = template[key]

    # Merge env (template priority)
    if "env" in template:
        result["env"] = {**existing.get("env", {}), **template["env"]}

    # Merge permissions (union, deduplicate, sorted)
    if "permissions" in template:
        existing_perms = existing.get("permissions", {})
        template_perms = template["permissions"]

        result["permissions"] = {
            "allow": sorted(set(
                existing_perms.get("allow", []) +
                template_perms.get("allow", [])
            )),
            "deny": sorted(set(
                existing_perms.get("deny", []) +
                template_perms.get("deny", [])
            )),
        }

        # Preserve 'ask' if it exists
        if "ask" in existing_perms:
            result["permissions"]["ask"] = existing_perms["ask"]

    return result


def diff_settings(project_config: dict, installed_config: dict) -> DiffResult:
    """Compare project config with installed ~/.claude/settings.json.

    Returns a DiffResult showing what's different between them.
    """
    result = DiffResult()

    # Keys to compare
    all_keys = set(project_config.keys()) | set(installed_config.keys())

    for key in all_keys:
        proj_val = project_config.get(key)
        inst_val = installed_config.get(key)

        if key not in project_config:
            result.added.append(f"settings.{key}")
        elif key not in installed_config:
            result.removed.append(f"settings.{key}")
        elif proj_val != inst_val:
            result.modified.append(f"settings.{key}")
        else:
            result.unchanged.append(f"settings.{key}")

    return result


def diff_skills(project_skills_dir: Path, installed_skills_dir: Path) -> DiffResult:
    """Compare skills directories.

    Returns a DiffResult showing new/modified/deleted skills.
    """
    result = DiffResult()

    project_skills = set()
    installed_skills = set()

    if project_skills_dir.exists():
        project_skills = {d.name for d in project_skills_dir.iterdir() if d.is_dir()}
    if installed_skills_dir.exists():
        installed_skills = {d.name for d in installed_skills_dir.iterdir() if d.is_dir()}

    # New skills (in installed but not in project)
    for skill in installed_skills - project_skills:
        result.added.append(f"skill:{skill}")

    # Removed skills (in project but not in installed)
    for skill in project_skills - installed_skills:
        result.removed.append(f"skill:{skill}")

    # Check for modified skills (exist in both)
    for skill in project_skills & installed_skills:
        proj_path = project_skills_dir / skill
        inst_path = installed_skills_dir / skill

        # Simple modification check: compare file counts and main skill file
        proj_files = list(proj_path.rglob("*"))
        inst_files = list(inst_path.rglob("*"))

        if len(proj_files) != len(inst_files):
            result.modified.append(f"skill:{skill}")
        else:
            # Check if main skill file differs
            skill_file_names = ["skill.md", "SKILL.md"]
            modified = False
            for fname in skill_file_names:
                proj_file = proj_path / fname
                inst_file = inst_path / fname
                if proj_file.exists() and inst_file.exists():
                    if proj_file.read_text() != inst_file.read_text():
                        modified = True
                        break
            if modified:
                result.modified.append(f"skill:{skill}")
            else:
                result.unchanged.append(f"skill:{skill}")

    return result


def export_settings(
    installed_path: Path,
    project_path: Path,
    dry_run: bool = False,
    console: Console | None = None,
) -> tuple[bool, Path | None]:
    """Export settings from ~/.claude/settings.json to config/settings.json.

    Returns (success, backup_path).
    """
    if not installed_path.exists():
        if console:
            console.print(f"  [yellow]No installed settings found at {installed_path}[/yellow]")
        return False, None

    try:
        with open(installed_path, 'r') as f:
            installed = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        if console:
            console.print(f"  [red]Failed to read installed settings:[/red] {e}")
        return False, None

    if dry_run:
        if console:
            console.print(f"  [dim]Would export settings to {project_path}[/dim]")
        return True, None

    # Create backup of project config
    backup_path = None
    if project_path.exists():
        backup_path = backup_file(project_path, console)
        if backup_path is None:
            return False, None

    # Write exported settings
    try:
        project_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = project_path.with_suffix(".tmp")
        with open(temp_path, 'w') as f:
            json.dump(installed, f, indent=2)
            f.write('\n')
        temp_path.replace(project_path)
        if console:
            console.print(f"  [green]Exported settings to {project_path}[/green]")
        return True, backup_path
    except Exception as e:
        if console:
            console.print(f"  [red]Failed to write:[/red] {e}")
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, project_path)
        return False, backup_path


def export_skills(
    installed_dir: Path,
    project_dir: Path,
    dry_run: bool = False,
    console: Console | None = None,
) -> list[str]:
    """Export new skills from ~/.claude/skills/ to project skills directory.

    Returns list of exported skill names.
    """
    exported = []

    if not installed_dir.exists():
        if console:
            console.print(f"  [yellow]No installed skills directory at {installed_dir}[/yellow]")
        return exported

    project_skills = set()
    if project_dir.exists():
        project_skills = {d.name for d in project_dir.iterdir() if d.is_dir()}

    for skill_path in installed_dir.iterdir():
        if not skill_path.is_dir():
            continue

        skill_name = skill_path.name
        dest_path = project_dir / skill_name

        # Only export skills that don't exist in project
        if skill_name in project_skills:
            continue

        if dry_run:
            if console:
                console.print(f"  [dim]Would export skill:[/dim] {skill_name}")
            exported.append(skill_name)
            continue

        try:
            project_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill_path, dest_path)
            exported.append(skill_name)
            if console:
                console.print(f"  [green]Exported skill:[/green] {skill_name}")
        except Exception as e:
            if console:
                console.print(f"  [red]Failed to export {skill_name}:[/red] {e}")

    return exported


def export_plugins_state(
    installed_settings: dict,
    project_plugins_path: Path,
    dry_run: bool = False,
    console: Console | None = None,
) -> tuple[bool, Path | None]:
    """Export enabled/disabled plugin states from installed settings to project plugins.json.

    Returns (success, backup_path).
    """
    installed_enabled = installed_settings.get("enabledPlugins", {})
    if not installed_enabled:
        if console:
            console.print("  [dim]No enabledPlugins in installed settings[/dim]")
        return True, None

    # Read existing plugins config
    if not project_plugins_path.exists():
        if console:
            console.print(f"  [yellow]No plugins config at {project_plugins_path}[/yellow]")
        return False, None

    try:
        with open(project_plugins_path, 'r') as f:
            plugins_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        if console:
            console.print(f"  [red]Failed to read plugins config:[/red] {e}")
        return False, None

    # Update enabled states
    updated = False
    for plugin in plugins_data.get("plugins", []):
        key = f"{plugin['name']}@{plugin['marketplace']}"
        if key in installed_enabled:
            new_state = installed_enabled[key]
            if plugin.get("enabled") != new_state:
                plugin["enabled"] = new_state
                updated = True

    if not updated:
        if console:
            console.print("  [dim]No plugin state changes[/dim]")
        return True, None

    if dry_run:
        if console:
            console.print(f"  [dim]Would update plugin states in {project_plugins_path}[/dim]")
        return True, None

    # Create backup
    backup_path = backup_file(project_plugins_path, console)

    # Write updated config
    try:
        temp_path = project_plugins_path.with_suffix(".tmp")
        with open(temp_path, 'w') as f:
            json.dump(plugins_data, f, indent=2)
            f.write('\n')
        temp_path.replace(project_plugins_path)
        if console:
            console.print(f"  [green]Updated plugin states in {project_plugins_path}[/green]")
        return True, backup_path
    except Exception as e:
        if console:
            console.print(f"  [red]Failed to write:[/red] {e}")
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, project_plugins_path)
        return False, backup_path


def setup_settings(
    template: dict,
    settings_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    console: Console | None = None,
) -> tuple[bool, str, Path | None]:
    """Configure settings file with template. Returns (success, status, backup_path)."""
    global _completed_steps

    if console and not quiet:
        console.print(f"\n[bold]Configuring {settings_path.name}...[/bold]")

    # Read existing settings
    existing = {}
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                existing = json.load(f)
        except json.JSONDecodeError as e:
            if console and not quiet:
                console.print(f"  [red]Invalid JSON in existing file:[/red] {e}")
            return False, f"invalid JSON: {e}", None

    # Merge settings
    merged = merge_settings(existing, template)

    if dry_run:
        if console and not quiet:
            console.print(f"  [dim]Would update {settings_path}[/dim]")
            if verbose:
                console.print(f"  [dim]{json.dumps(merged, indent=2)}[/dim]")
        return True, "would update", None

    # Create backup of existing file
    backup_path = None
    if settings_path.exists():
        backup_path = backup_file(settings_path, console if verbose else None)
        if backup_path is None:
            return False, "backup failed", None

    # Write merged settings
    try:
        # Ensure parent directory exists
        settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with atomic operation via temp file
        temp_path = settings_path.with_suffix(".tmp")
        with open(temp_path, 'w') as f:
            json.dump(merged, f, indent=2)
            f.write('\n')  # Add trailing newline

        # Atomic rename
        temp_path.replace(settings_path)

        _completed_steps.append(f"settings:{settings_path.name}")
        if console and not quiet:
            console.print(f"  {settings_path.name}: [green]configured[/green]")

        return True, "configured", backup_path

    except Exception as e:
        if console and not quiet:
            console.print(f"  [red]Failed to write:[/red] {e}")
        # Restore backup if write failed
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, settings_path)
            if console and not quiet:
                console.print(f"  [yellow]Restored from backup[/yellow]")
        return False, f"write failed: {e}", backup_path


def print_summary(
    result: SetupResult,
    console: Console,
) -> None:
    """Print a summary table of the setup."""
    console.print("\n")

    table = Table(title="Setup Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Status")

    for plugin, status in result.plugins.items():
        if "installed" in status:
            styled = "[green]Installed[/green]"
        else:
            styled = "[red]Failed[/red]"
        table.add_row(f"Plugin: {plugin}", styled)

    for skill, status in result.skills.items():
        if "created" in status:
            styled = "[green]Created[/green]"
        elif "skipped" in status:
            styled = "[cyan]Skipped[/cyan]"
        else:
            styled = "[red]Failed[/red]"
        table.add_row(f"Skill: {skill}", styled)

    for settings_file, status in result.settings.items():
        if "configured" in status or "updated" in status:
            styled = "[green]Configured[/green]"
        elif "skipped" in status or "would" in status:
            styled = "[cyan]Skipped[/cyan]"
        else:
            styled = "[red]Failed[/red]"
        table.add_row(f"Settings: {settings_file}", styled)

    console.print(table)

    # Calculate totals
    total_plugins = len(result.plugins)
    success_plugins = sum(1 for s in result.plugins.values() if "failed" not in s.lower())

    if result.exit_code == EXIT_SUCCESS:
        console.print("\n[green bold]Setup completed successfully![/green bold]")
    else:
        console.print(
            f"\n[yellow]Setup completed with issues: "
            f"{success_plugins}/{total_plugins} plugins OK[/yellow]"
        )

    # Next steps (critical info at end per CLI guidelines)
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Restart Claude Code to load new configuration")
    console.print("  2. Run [cyan]/claude-hud:setup[/cyan] if status line isn't working")
    console.print("  3. Verify settings: [cyan]cat ~/.claude/settings.json[/cyan]")
    if result.backups:
        console.print(f"  4. Backups saved: {', '.join(result.backups)}")


def run_status(
    console: Console,
    err_console: Console,
    quiet: bool = False,
    json_output: bool = False,
) -> int:
    """Show differences between project config and installed config."""
    installed_settings_path = Path.home() / ".claude" / "settings.json"
    installed_skills_path = Path.home() / ".claude" / "skills"
    project_settings_path = CONFIG_DIR / "settings.json"

    # Load configs
    project_config = load_settings_template()
    installed_config = {}
    if installed_settings_path.exists():
        try:
            with open(installed_settings_path, 'r') as f:
                installed_config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Diff settings
    settings_diff = diff_settings(project_config, installed_config)

    # Diff skills
    skills_diff = diff_skills(SKILLS_DIR, installed_skills_path)

    # Combine results
    combined = DiffResult(
        added=settings_diff.added + skills_diff.added,
        removed=settings_diff.removed + skills_diff.removed,
        modified=settings_diff.modified + skills_diff.modified,
        unchanged=settings_diff.unchanged + skills_diff.unchanged,
    )

    if json_output:
        print(json.dumps({
            "settings": settings_diff.to_dict(),
            "skills": skills_diff.to_dict(),
            "combined": combined.to_dict(),
        }, indent=2))
        return EXIT_DRIFT_DETECTED if combined.has_drift else EXIT_SUCCESS

    if not quiet:
        console.print("\n[bold]Configuration Status[/bold]")
        console.print(f"  Project config: {project_settings_path}")
        console.print(f"  Installed config: {installed_settings_path}\n")

        if not combined.has_drift:
            console.print("[green]No drift detected - configurations are in sync[/green]")
            return EXIT_SUCCESS

        table = Table(title="Drift Report")
        table.add_column("Type", style="cyan")
        table.add_column("Item")
        table.add_column("Status")

        for item in combined.added:
            table.add_row("Added", item, "[yellow]In installed, not in project[/yellow]")
        for item in combined.removed:
            table.add_row("Removed", item, "[red]In project, not in installed[/red]")
        for item in combined.modified:
            table.add_row("Modified", item, "[blue]Values differ[/blue]")

        console.print(table)
        console.print(f"\n[yellow]Drift detected: {len(combined.added)} added, "
                     f"{len(combined.removed)} removed, {len(combined.modified)} modified[/yellow]")

    return EXIT_DRIFT_DETECTED if combined.has_drift else EXIT_SUCCESS


def run_export(
    console: Console,
    err_console: Console,
    dry_run: bool = False,
    diff_only: bool = False,
    quiet: bool = False,
    json_output: bool = False,
) -> int:
    """Export changes from ~/.claude/ back to project config."""
    result = ExportResult()

    installed_settings_path = Path.home() / ".claude" / "settings.json"
    installed_skills_path = Path.home() / ".claude" / "skills"
    project_settings_path = CONFIG_DIR / "settings.json"
    project_plugins_path = CONFIG_DIR / "plugins.json"

    if not quiet and not json_output:
        console.print("\n[bold]Exporting configuration from ~/.claude/[/bold]")
        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
        if diff_only:
            console.print("[cyan]DIFF ONLY - Showing changes without applying[/cyan]\n")

    # Show diff if requested
    if diff_only:
        return run_status(console, err_console, quiet, json_output)

    # Export settings
    if not quiet and not json_output:
        console.print("\n[bold]Exporting settings...[/bold]")
    success, backup_path = export_settings(
        installed_settings_path,
        project_settings_path,
        dry_run,
        console if not quiet and not json_output else None,
    )
    result.settings_exported = success
    if backup_path:
        result.backups.append(str(backup_path))

    # Export new skills
    if not quiet and not json_output:
        console.print("\n[bold]Exporting skills...[/bold]")
    exported_skills = export_skills(
        installed_skills_path,
        SKILLS_DIR,
        dry_run,
        console if not quiet and not json_output else None,
    )
    result.skills_exported = exported_skills

    # Export plugin states
    if not quiet and not json_output:
        console.print("\n[bold]Exporting plugin states...[/bold]")

    installed_settings = {}
    if installed_settings_path.exists():
        try:
            with open(installed_settings_path, 'r') as f:
                installed_settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    plugin_success, plugin_backup = export_plugins_state(
        installed_settings,
        project_plugins_path,
        dry_run,
        console if not quiet and not json_output else None,
    )
    result.plugins_exported = plugin_success
    if plugin_backup:
        result.backups.append(str(plugin_backup))

    # Determine exit code
    if not result.settings_exported:
        result.exit_code = EXIT_EXPORT_FAILED

    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
    elif not quiet and not dry_run:
        console.print("\n[green bold]Export completed![/green bold]")
        if result.backups:
            console.print(f"[dim]Backups: {', '.join(result.backups)}[/dim]")

    return result.exit_code


def run_sync(
    args,
    console: Console,
    err_console: Console,
    quiet: bool = False,
    json_output: bool = False,
) -> int:
    """Bidirectional sync: export then setup."""
    if not quiet and not json_output:
        console.print("\n[bold]Bidirectional Sync[/bold]")
        console.print("Step 1: Exporting changes from ~/.claude/ to project...")

    # Run export first
    export_result = run_export(
        console,
        err_console,
        dry_run=args.dry_run,
        diff_only=False,
        quiet=quiet,
        json_output=False,  # We'll output combined JSON at the end
    )

    if export_result != EXIT_SUCCESS and export_result != EXIT_DRIFT_DETECTED:
        if not quiet and not json_output:
            err_console.print("[red]Export failed, aborting sync[/red]")
        return EXIT_SYNC_FAILED

    if not quiet and not json_output:
        console.print("\nStep 2: Pushing project config to ~/.claude/...")

    # The rest of the setup will happen in main()
    # Return a special code to indicate we should continue with setup
    return EXIT_SUCCESS


def main() -> int:
    # Set up signal handler for Ctrl-C
    signal.signal(signal.SIGINT, handle_interrupt)

    # Check for quiet mode via environment
    env_quiet = os.environ.get("CLAUDE_SETUP_QUIET", "").lower() in ("1", "true", "yes")

    parser = argparse.ArgumentParser(
        description="Set up Claude Code with a curated configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run setup_claude_code.py              # Run full setup
  uv run setup_claude_code.py --dry-run    # Preview changes
  uv run setup_claude_code.py --json       # Output results as JSON
  uv run setup_claude_code.py --skip-plugins  # Only install skills

Sync commands:
  uv run setup_claude_code.py --status     # Show drift between project and installed
  uv run setup_claude_code.py --export     # Pull changes from ~/.claude/ to project
  uv run setup_claude_code.py --export --diff  # Show diff only
  uv run setup_claude_code.py --sync       # Bidirectional: export then setup

Environment variables:
  NO_COLOR=1              Disable colored output
  CLAUDE_SETUP_QUIET=1    Suppress non-essential output

For issues: https://github.com/anthropics/claude-code/issues
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--skip-plugins",
        action="store_true",
        help="Skip plugin installation",
    )
    parser.add_argument(
        "--skip-skills",
        action="store_true",
        help="Skip skill creation",
    )
    parser.add_argument(
        "--skip-settings",
        action="store_true",
        help="Skip settings.json configuration",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed command output",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress non-essential output",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (implies --quiet)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show differences between project config and installed config",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export changes from ~/.claude/ back to project config",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Bidirectional sync: export changes then push configuration",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show diff only without making changes (use with --export)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Auto-accept all changes without prompting",
    )

    args = parser.parse_args()

    # JSON mode implies quiet
    quiet = args.quiet or args.json or env_quiet

    # Create consoles
    console = create_console(force_no_color=args.no_color, quiet=quiet)
    err_console = create_error_console(force_no_color=args.no_color)

    # Handle --status command
    if args.status:
        return run_status(console, err_console, quiet, args.json)

    # Handle --export command
    if args.export:
        return run_export(
            console, err_console,
            dry_run=args.dry_run,
            diff_only=args.diff,
            quiet=quiet,
            json_output=args.json,
        )

    # Handle --sync command (export first, then continue with setup)
    if args.sync:
        sync_result = run_sync(args, console, err_console, quiet, args.json)
        if sync_result != EXIT_SUCCESS:
            return sync_result
        # Continue with normal setup below

    result = SetupResult()

    # Header (skip in quiet/JSON mode)
    if not quiet:
        console.print(
            Panel.fit(
                "[bold blue]Claude Code Setup Script[/bold blue]\n"
                "[dim]Replicating a curated configuration[/dim]",
                border_style="blue",
            )
        )

        if args.dry_run:
            console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    # Check prerequisites
    if not args.dry_run and not check_prerequisites(console, err_console):
        result.exit_code = EXIT_MISSING_PREREQ
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        return result.exit_code

    # Install plugins
    if not args.skip_plugins:
        result.plugins = setup_plugins(args.dry_run, args.verbose, quiet, console)
        # Check for failures
        if any("failed" in s.lower() for s in result.plugins.values()):
            result.exit_code = EXIT_PLUGIN_FAILED
    elif not quiet:
        console.print("\n[dim]Skipping plugin installation[/dim]")

    # Setup skills
    if not args.skip_skills:
        result.skills = setup_skills(args.dry_run, args.verbose, quiet, console)
        # Check for failures
        if any("failed" in s.lower() for s in result.skills.values()):
            if result.exit_code == EXIT_SUCCESS:
                result.exit_code = EXIT_SKILL_FAILED
    elif not quiet:
        console.print("\n[dim]Skipping skill creation[/dim]")

    # Setup settings.json
    if not args.skip_settings:
        settings_path = Path.home() / ".claude" / "settings.json"
        settings_template = load_settings_template()
        # Merge with enabled plugins from external config
        enabled_plugins = load_enabled_plugins()
        if enabled_plugins:
            settings_template["enabledPlugins"] = enabled_plugins
        success, status, backup_path = setup_settings(
            settings_template,
            settings_path,
            args.dry_run,
            args.verbose,
            quiet,
            console
        )
        result.settings["settings.json"] = status
        if backup_path:
            result.backups.append(str(backup_path))
        if not success and "failed" in status.lower():
            result.exit_code = EXIT_SETTINGS_FAILED
    elif not quiet:
        console.print("\n[dim]Skipping settings.json configuration[/dim]")

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif not args.dry_run and not quiet:
        print_summary(result, console)

    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
