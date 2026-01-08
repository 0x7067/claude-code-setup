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
    ("dev-consultant", "alteredcraft-plugins", "AlteredCraft/claude-code-plugins"),
    ("claude-hud", "claude-hud", "jarrodwatts/claude-hud"),
    ("code-review", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("commit-commands", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("feature-dev", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("swift-lsp", "claude-plugins-official", "anthropics/claude-plugins-official"),
    ("mgrep", "Mixedbread-Grep", "mixedbread-ai/mgrep"),
]

DESIGN_PRINCIPLES_SKILL = '''---
name: design-principles
description: Enforce a precise, minimal design system inspired by Linear, Notion, and Stripe. Use this skill when building dashboards, admin interfaces, or any UI that needs Jony Ive-level precision - clean, modern, minimalist with taste. Every pixel matters.
---

# Design Principles

This skill enforces precise, crafted design for enterprise software, SaaS dashboards, admin interfaces, and web applications. The philosophy is Jony Ive-level precision with intentional personality — every interface is polished, and each is designed for its specific context.

## Design Direction (REQUIRED)

**Before writing any code, commit to a design direction.** Don't default. Think about what this specific product needs to feel like.

### Think About Context

- **What does this product do?** A finance tool needs different energy than a creative tool.
- **Who uses it?** Power users want density. Occasional users want guidance.
- **What's the emotional job?** Trust? Efficiency? Delight? Focus?
- **What would make this memorable?** Every product has a chance to feel distinctive.

### Choose a Personality

Enterprise/SaaS UI has more range than you think. Consider these directions:

**Precision & Density** — Tight spacing, monochrome, information-forward. For power users who live in the tool. Think Linear, Raycast, terminal aesthetics.

**Warmth & Approachability** — Generous spacing, soft shadows, friendly colors. For products that want to feel human. Think Notion, Coda, collaborative tools.

**Sophistication & Trust** — Cool tones, layered depth, financial gravitas. For products handling money or sensitive data. Think Stripe, Mercury, enterprise B2B.

**Boldness & Clarity** — High contrast, dramatic negative space, confident typography. For products that want to feel modern and decisive. Think Vercel, minimal dashboards.

**Utility & Function** — Muted palette, functional density, clear hierarchy. For products where the work matters more than the chrome. Think GitHub, developer tools.

**Data & Analysis** — Chart-optimized, technical but accessible, numbers as first-class citizens. For analytics, metrics, business intelligence.

Pick one. Or blend two. But commit to a direction that fits the product.

### Choose a Color Foundation

**Don't default to warm neutrals.** Consider the product:

- **Warm foundations** (creams, warm grays) — approachable, comfortable, human
- **Cool foundations** (slate, blue-gray) — professional, trustworthy, serious
- **Pure neutrals** (true grays, black/white) — minimal, bold, technical
- **Tinted foundations** (slight color cast) — distinctive, memorable, branded

**Light or dark?** Dark modes aren't just light modes inverted. Dark feels technical, focused, premium. Light feels open, approachable, clean. Choose based on context.

**Accent color** — Pick ONE that means something. Blue for trust. Green for growth. Orange for energy. Violet for creativity. Don't just reach for the same accent every time.

### Choose a Layout Approach

The content should drive the layout:

- **Dense grids** for information-heavy interfaces where users scan and compare
- **Generous spacing** for focused tasks where users need to concentrate
- **Sidebar navigation** for multi-section apps with many destinations
- **Top navigation** for simpler tools with fewer sections
- **Split panels** for list-detail patterns where context matters

### Choose Typography

Typography sets tone. Don't always default:

- **System fonts** — fast, native, invisible (good for utility-focused products)
- **Geometric sans** (Geist, Inter) — modern, clean, technical
- **Humanist sans** (SF Pro, Satoshi) — warmer, more approachable
- **Monospace influence** — technical, developer-focused, data-heavy

---

## Core Craft Principles

These apply regardless of design direction. This is the quality floor.

### The 4px Grid
All spacing uses a 4px base grid:
- `4px` - micro spacing (icon gaps)
- `8px` - tight spacing (within components)
- `12px` - standard spacing (between related elements)
- `16px` - comfortable spacing (section padding)
- `24px` - generous spacing (between sections)
- `32px` - major separation

### Symmetrical Padding
**TLBR must match.** If top padding is 16px, left/bottom/right must also be 16px. Exception: when content naturally creates visual balance.

```css
/* Good */
padding: 16px;
padding: 12px 16px; /* Only when horizontal needs more room */

/* Bad */
padding: 24px 16px 12px 16px;
```

### Border Radius Consistency
Stick to the 4px grid. Sharper corners feel technical, rounder corners feel friendly. Pick a system and commit:

- Sharp: 4px, 6px, 8px
- Soft: 8px, 12px
- Minimal: 2px, 4px, 6px

Don't mix systems. Consistency creates coherence.

### Depth & Elevation Strategy

**Match your depth approach to your design direction.** Depth is a tool, not a requirement. Different products need different approaches:

**Borders-only (flat)** — Clean, technical, dense. Works for utility-focused tools where information density matters more than visual lift. Linear, Raycast, and many developer tools use almost no shadows — just subtle borders to define regions. This isn't lazy; it's intentional restraint.

**Subtle single shadows** — Soft lift without complexity. A simple `0 1px 3px rgba(0,0,0,0.08)` can be enough. Works for approachable products that want gentle depth without the weight of layered shadows.

**Layered shadows** — Rich, premium, dimensional. Multiple shadow layers create realistic depth for products that want to feel substantial. Stripe and Mercury use this approach. Best for cards that need to feel like physical objects.

**Surface color shifts** — Background tints establish hierarchy without any shadows. A card at `#fff` on a `#f8fafc` background already feels elevated. Shadows can reinforce this, but color does the heavy lifting.

Choose ONE approach and commit. Mixing flat borders on some cards with heavy shadows on others creates visual inconsistency.

```css
/* Borders-only approach */
--border: rgba(0, 0, 0, 0.08);
--border-subtle: rgba(0, 0, 0, 0.05);
border: 0.5px solid var(--border);

/* Single shadow approach */
--shadow: 0 1px 3px rgba(0, 0, 0, 0.08);

/* Layered shadow approach (when appropriate) */
--shadow-layered:
  0 0 0 0.5px rgba(0, 0, 0, 0.05),
  0 1px 2px rgba(0, 0, 0, 0.04),
  0 2px 4px rgba(0, 0, 0, 0.03),
  0 4px 8px rgba(0, 0, 0, 0.02);
```

**The craft is in the choice, not the complexity.** A flat interface with perfect spacing and typography is more polished than a shadow-heavy interface with sloppy details.

### Card Layouts Vary, Surface Treatment Stays Consistent
Monotonous card layouts are lazy design. A metric card doesn't have to look like a plan card doesn't have to look like a settings card. One might have a sparkline, another an avatar stack, another a progress ring, another a two-column split.

Design each card's internal structure for its specific content — but keep the surface treatment consistent: same border weight, shadow depth, corner radius, padding scale, typography. Cohesion comes from the container chrome, not from forcing every card into the same layout template.

### Isolated Controls
UI controls deserve container treatment. Date pickers, filters, dropdowns — these should feel like crafted objects sitting on the page, not plain text with click handlers.

**Never use native form elements for styled UI.** Native `<select>`, `<input type="date">`, and similar elements render OS-native dropdowns and pickers that cannot be styled. Build custom components instead:

- Custom select: trigger button + positioned dropdown menu
- Custom date picker: input + calendar popover
- Custom checkbox/radio: styled div with state management

**Custom select triggers must use `display: inline-flex` with `white-space: nowrap`** to keep text and chevron icons on the same row. Without this, flex children can wrap to new lines.

### Typography Hierarchy
- Headlines: 600 weight, tight letter-spacing (-0.02em)
- Body: 400-500 weight, standard tracking
- Labels: 500 weight, slight positive tracking for uppercase
- Scale: 11px, 12px, 13px, 14px (base), 16px, 18px, 24px, 32px

### Monospace for Data
Numbers, IDs, codes, timestamps belong in monospace. Use `tabular-nums` for columnar alignment. Mono signals "this is data."

### Iconography
Use **Phosphor Icons** (`@phosphor-icons/react`). Icons clarify, not decorate — if removing an icon loses no meaning, remove it.

Give standalone icons presence with subtle background containers.

### Animation
- 150ms for micro-interactions, 200-250ms for larger transitions
- Easing: `cubic-bezier(0.25, 1, 0.5, 1)`
- No spring/bouncy effects in enterprise UI

### Contrast Hierarchy
Build a four-level system: foreground (primary) → secondary → muted → faint. Use all four consistently.

### Color for Meaning Only
Gray builds structure. Color only appears when it communicates: status, action, error, success. Decorative color is noise.

When building data-heavy interfaces, ask whether each use of color is earning its place. Score bars don't need to be color-coded by performance — a single muted color works. Grade badges don't need traffic-light colors — typography can do the hierarchy work. Look at how GitHub renders tables and lists: almost entirely monochrome, with color reserved for status indicators and actionable elements.

---

## Navigation Context

Screens need grounding. A data table floating in space feels like a component demo, not a product. Consider including:

- **Navigation** — sidebar or top nav showing where you are in the app
- **Location indicator** — breadcrumbs, page title, or active nav state
- **User context** — who's logged in, what workspace/org

When building sidebars, consider using the same background as the main content area. Tools like Supabase, Linear, and Vercel rely on a subtle border for separation rather than different background colors. This reduces visual weight and feels more unified.

---

## Dark Mode Considerations

Dark interfaces have different needs:

**Borders over shadows** — Shadows are less visible on dark backgrounds. Lean more on borders for definition. A border at 10-15% white opacity might look nearly invisible but it's doing its job — resist the urge to make it more prominent.

**Adjust semantic colors** — Status colors (success, warning, error) often need to be slightly desaturated or adjusted for dark backgrounds to avoid feeling harsh.

**Same structure, different values** — The hierarchy system (foreground → secondary → muted → faint) still applies, just with inverted values.

---

## Anti-Patterns

### Never Do This
- Dramatic drop shadows (`box-shadow: 0 25px 50px...`)
- Large border radius (16px+) on small elements
- Asymmetric padding without clear reason
- Pure white cards on colored backgrounds
- Thick borders (2px+) for decoration
- Excessive spacing (margins > 48px between sections)
- Spring/bouncy animations
- Gradients for decoration
- Multiple accent colors in one interface

### Always Question
- "Did I think about what this product needs, or did I default?"
- "Does this direction fit the context and users?"
- "Does this element feel crafted?"
- "Is my depth strategy consistent and intentional?"
- "Are all elements on the grid?"

---

## The Standard

Every interface should look designed by a team that obsesses over 1-pixel differences. Not stripped — *crafted*. And designed for its specific context.

Different products want different things. A developer tool wants precision and density. A collaborative product wants warmth and space. A financial product wants trust and sophistication. Let the product context guide the aesthetic.

The goal: intricate minimalism with appropriate personality. Same quality bar, context-driven execution.
'''

# Settings.json template with full configuration
SETTINGS_TEMPLATE = {
    "model": "sonnet",
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
        "dev-consultant@alteredcraft-plugins": True,
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

    # Get unique marketplaces
    marketplaces = {}
    for plugin, marketplace, repo in PLUGINS:
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

    for plugin, marketplace, _ in PLUGINS:
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
    """Create skill files. Returns dict of skill name -> status."""
    global _completed_steps
    results: dict[str, str] = {}

    if console and not quiet:
        console.print("\n[bold]Setting up skills...[/bold]")

    skills_dir = Path.home() / ".claude" / "skills" / "design-principles"
    skill_file = skills_dir / "skill.md"

    # Check if already exists (idempotent)
    if skill_file.exists() and not dry_run:
        results["design-principles"] = "skipped (already exists)"
        if console and not quiet:
            console.print(f"  design-principles: [cyan]skipped[/cyan] (already exists)")
        return results

    if dry_run:
        if console and not quiet:
            console.print(f"  [dim]Would create:[/dim] {skill_file}")
        results["design-principles"] = "would create"
        return results

    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(DESIGN_PRINCIPLES_SKILL)
        results["design-principles"] = "created"
        _completed_steps.append("skill:design-principles")
        if console and not quiet:
            console.print(f"  design-principles: [green]created[/green]")
    except Exception as e:
        results["design-principles"] = f"failed: {e}"
        if console and not quiet:
            console.print(f"  design-principles: [red]failed[/red] - {e}")

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

    - Simple keys (model, alwaysThinkingEnabled): template overrides
    - env: merge with template priority
    - permissions: union of allow/deny lists
    - hooks, statusLine, enabledPlugins: template overrides
    - Unknown keys: preserved from existing
    """
    result = existing.copy()

    # Direct overrides
    for key in ["model", "alwaysThinkingEnabled", "hooks", "statusLine", "enabledPlugins"]:
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
  uv run ~/setup-claude-code.py              # Run full setup
  uv run ~/setup-claude-code.py --dry-run    # Preview changes
  uv run ~/setup-claude-code.py --json       # Output results as JSON
  uv run ~/setup-claude-code.py --skip-plugins  # Only install skills

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

    args = parser.parse_args()

    # JSON mode implies quiet
    quiet = args.quiet or args.json or env_quiet

    # Create consoles
    console = create_console(force_no_color=args.no_color, quiet=quiet)
    err_console = create_error_console(force_no_color=args.no_color)

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
        success, status, backup_path = setup_settings(
            SETTINGS_TEMPLATE,
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
