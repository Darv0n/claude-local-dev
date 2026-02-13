# claude-local-dev

CLI tool for managing a local-dev marketplace for Claude Code plugins.

Claude Code's plugin loader only auto-loads plugins registered through a marketplace.
There is no official local development marketplace. This tool automates the process of
creating one — replacing 10+ manual steps with single commands.

## Install

```bash
cd claude-local-dev
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"   # Windows
# or: .venv/bin/pip install -e ".[dev]"  # Unix
```

## Usage

```bash
# Create the local-dev marketplace
claude-local-dev init

# Register a plugin from a local directory
claude-local-dev add /path/to/my-plugin

# List registered plugins with status
claude-local-dev list

# Verify consistency across all registry files
claude-local-dev verify

# Unregister a plugin
claude-local-dev remove my-plugin
```

## What It Does

Each command manages the three JSON files that Claude Code's plugin loader reads:

| File | What We Touch |
|------|--------------|
| `~/.claude/settings.json` | `enabledPlugins` entries |
| `~/.claude/plugins/installed_plugins.json` | Plugin install records |
| `~/.claude/plugins/known_marketplaces.json` | Marketplace registration |

The `add` command also creates an NTFS junction (Windows) or symlink (Unix) from the
marketplace plugins directory to your plugin source directory, so edits are live.

All operations preserve existing data (hooks, official marketplace entries, other plugins).

## Development

```bash
# Run tests
.venv/Scripts/pytest -v

# Run with coverage
.venv/Scripts/pytest --cov
```
