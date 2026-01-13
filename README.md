# Claude Code Setup

Custom skills and configuration for Claude Code (claude.ai/code).

## Requirements
- `fd` (install with `brew install fd`)
- `rg` (install with `brew install ripgrep`)
- `jq` (install with `brew install jq`)
- Linear plugin for Claude Code (run `/plugin install linear@claude-plugins-official` in Claude Code)

## Installation

Clone and copy to your global Claude Code config directory:

```bash
# Backup first if you have existing config
cp -r ~/.claude ~/.claude.backup

# Clone this repo
git clone https://github.com/0x7067/claude-code-setup.git

# Copy to your global Claude config
cp -r claude-code-setup/.claude ~/.claude
```

### Existing Installation

## What's Included

- **Skills:** design-principles, swift-concurrency, design-patterns, feedback-to-linear
- **Settings:** Pre-configured permissions (git, docker, build tools)
- **Model preference:** opusplan

## Skills

| Skill | Description |
|-------|-------------|
| design-principles | UI/UX design system (Linear/Notion/Stripe-inspired) |
| swift-concurrency | Swift async/await, actors, Swift 6 migration |
| design-patterns | Gang of Four pattern selection |
| feedback-to-linear | Convert feedback to Linear issues |

## Customization

Edit `~/.claude/settings.json` to adjust permissions, model, or enabled features.
