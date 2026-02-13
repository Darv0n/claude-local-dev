# claude-local-dev

## What This Is

CLI tool that manages a "local-dev" marketplace for Claude Code plugins.
Replaces 10+ manual steps (creating directories, NTFS junctions, editing
three JSON files) with single commands.

## Architecture

```
cli.py --> commands/* --> registry.py --> models.py
                     --> junction.py     config.py
                                         errors.py
```

Dependency flow is strictly downward. No circular imports.

## Critical Constraint

settings.json contains hooks and other keys we don't own. installed_plugins.json
and known_marketplaces.json contain official marketplace entries. All mutations
use read-modify-write: read full file, change only our keys, write back.

## Testing

```bash
.venv/Scripts/pytest          # Run all tests
.venv/Scripts/pytest -v       # Verbose output
.venv/Scripts/pytest --cov    # With coverage
```

All tests use CLAUDE_CONFIG_DIR env var to isolate from real ~/.claude.

## Three JSON Files

1. `~/.claude/settings.json` — enabledPlugins (+ hooks, autoUpdatesChannel)
2. `~/.claude/plugins/installed_plugins.json` — plugin install records
3. `~/.claude/plugins/known_marketplaces.json` — marketplace registry
