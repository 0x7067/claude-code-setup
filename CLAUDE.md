# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains `setup_claude_code.py`, a Python script that automates the installation and configuration of Claude Code with a curated set of plugins, skills, and settings.

**Key design principle**: The script is fully idempotent - it can be safely run multiple times without breaking existing configurations or duplicating resources.

## Running the Script

The script is designed to be run with `uv`:

```bash
# Full setup (push config to ~/.claude/)
uv run setup_claude_code.py

# Preview changes without making them
uv run setup_claude_code.py --dry-run

# Output results as JSON
uv run setup_claude_code.py --json

# Skip specific components
uv run setup_claude_code.py --skip-plugins
uv run setup_claude_code.py --skip-skills
uv run setup_claude_code.py --skip-settings
```

## Sync Commands

The script supports bidirectional sync between the project config and your installed Claude Code configuration:

```bash
# Show drift between project config and installed config
uv run setup_claude_code.py --status

# Export changes from ~/.claude/ back to project config
uv run setup_claude_code.py --export

# Show diff only (without making changes)
uv run setup_claude_code.py --export --diff

# Bidirectional sync: export changes then push config
uv run setup_claude_code.py --sync
```

### Periodic Sync Workflow

To keep your project in sync with manual changes made to Claude Code:

1. **Check for drift**: `uv run setup_claude_code.py --status`
2. **Pull changes**: `uv run setup_claude_code.py --export` (creates backups automatically)
3. **Commit changes**: Review and commit the updated config files

## Development

### Dependencies

This project uses `uv` for dependency management. Dependencies are declared in `pyproject.toml`:
- **Runtime**: `rich>=13.0.0` for terminal output
- **Testing**: `pytest`, `pytest-cov`, `pytest-mock`

### Running Tests

The project includes comprehensive unit tests with 95% code coverage. Test files are located in the `tests/` directory:

```bash
# Install dependencies (if not already installed)
uv sync

# Run all tests
uv run pytest -v

# Run with coverage report
uv run pytest --cov=. --cov-report=term-missing --cov-report=html

# Run specific test file
uv run pytest tests/test_settings.py -v

# Run specific test
uv run pytest tests/test_settings.py::TestMergeSettings::test_env_merge_template_priority -v
```

View detailed coverage report:
```bash
open htmlcov/index.html  # macOS
```

### Test Structure

Tests are organized by functionality:
- `test_command.py` - Command execution
- `test_config_loading.py` - External config file loading
- `test_console.py` - Console output and color handling
- `test_diff.py` - Diff/status functionality
- `test_exit_codes.py` - Exit code validation
- `test_export.py` - Export functionality
- `test_file_operations.py` - File backup and atomic writes
- `test_main.py` - CLI argument parsing and main flow
- `test_plugins.py` - Plugin installation
- `test_settings.py` - Settings merging logic
- `test_skills.py` - Skill creation
- `conftest.py` - Shared pytest fixtures

## Architecture

### Project Structure

```
claude-code-setup/
├── config/
│   ├── settings.json       # Settings template (externalized)
│   └── plugins.json        # Plugins list with enabled state
├── skills/
│   ├── design-principles/  # Skill directories
│   └── swift-concurrency/
├── tests/                  # Unit tests
├── setup_claude_code.py    # Main script
└── CLAUDE.md
```

### Script Structure

The script is organized into several key components:

1. **External Configuration** (`config/` directory):
   - `config/settings.json`: Settings template (loaded by `load_settings_template()`)
   - `config/plugins.json`: Plugin list with enabled states (loaded by `load_plugins_config()`)
   - Falls back to embedded defaults if config files are missing

2. **Core Functions**:
   - `setup_plugins()`: Installs plugins from configured marketplaces
   - `setup_skills()`: Creates skill files in `~/.claude/skills/`
   - `setup_settings()`: Merges and updates `~/.claude/settings.json`
   - `merge_settings()`: Intelligent merging strategy for settings

3. **Sync Functions**:
   - `diff_settings()`: Compares project config with installed config
   - `diff_skills()`: Compares skill directories
   - `export_settings()`: Exports installed settings to project config
   - `export_skills()`: Exports new installed skills to project
   - `export_plugins_state()`: Updates plugin enabled states from installed

4. **CLI & Output**:
   - Uses `rich` library for formatted console output
   - Supports `--no-color` and respects `NO_COLOR` environment variable
   - JSON output mode for programmatic usage

### Settings Merge Strategy

The script uses intelligent merging when updating settings.json:

- **Direct overrides**: `model`, `alwaysThinkingEnabled`, `hooks`, `statusLine`, `enabledPlugins`
- **Merge with template priority**: `env` dictionary
- **Union merge**: `permissions.allow` and `permissions.deny` (deduplicated and sorted)
- **Preserved**: Unknown keys from existing settings

### Idempotency

The script is designed to be idempotent:
- Plugin installs succeed if already installed (updates to latest version)
- Skills are skipped if they already exist
- Settings are merged, not replaced
- Backups are created before modifying existing settings

### Exit Codes

```
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_MISSING_PREREQ = 2
EXIT_PLUGIN_FAILED = 3
EXIT_SKILL_FAILED = 4
EXIT_SETTINGS_FAILED = 5
EXIT_EXPORT_FAILED = 6
EXIT_SYNC_FAILED = 7
EXIT_DRIFT_DETECTED = 8  # Returned by --status when drift found
```

### Error Handling

- Graceful Ctrl-C handling with partial progress tracking
- Atomic file writes using temp files + rename
- Automatic backup restoration on write failure
- Command timeouts (default 120s)

## Plugin Configuration

The script installs these plugins:

- `claude-mem` (disabled by default)
- `plannotator`
- `dev-consultant`
- `claude-hud`
- `code-review`
- `commit-commands`
- `feature-dev`
- `swift-lsp`
- `mgrep` (disabled by default)

## Permissions Template

The settings template includes pre-approved permissions for:
- npm/yarn/pnpm commands
- git operations
- File operations (ls, cat, grep, find, etc.)
- Programming language tools (node, python, cargo, go, make)
- Docker commands
- Swift/Xcode toolchain

And denies access to sensitive files:
- `.env` and `.env.*` files
- `.envrc`, `./secrets/**`
- AWS, SSH, Kubernetes, npm, and netrc credentials

## Modifying Configuration

### Adding New Plugins

Edit `config/plugins.json` to add a new plugin:
```json
{
  "plugins": [
    ...existing plugins...
    {
      "name": "plugin-name",
      "marketplace": "marketplace-name",
      "repo": "github-org/repo-name",
      "enabled": true
    }
  ]
}
```

### Adding New Skills

Create a new directory in `skills/`:
```
skills/
└── my-new-skill/
    └── skill.md
```

The skill will be automatically installed to `~/.claude/skills/my-new-skill/`.

### Modifying Settings Template

Edit `config/settings.json` directly. Changes will be merged intelligently with existing settings when running setup.

## Important Implementation Details

### Command Execution
The `run_command()` function (lines 494-524) handles subprocess execution with:
- Configurable timeouts (default 120s)
- Dry-run support for previewing changes
- Verbose output mode
- Combined stdout/stderr capture

### Atomic File Writes
Settings updates use atomic writes via temp files (lines 766-772):
1. Write to `.tmp` file
2. Atomic rename to final destination
3. Automatic backup restoration on failure

This prevents corrupted settings if the write operation is interrupted.

### Prerequisites
The script requires the `claude` CLI to be installed. Check with `claude --version` or install from https://docs.anthropic.com/en/docs/claude-code.
