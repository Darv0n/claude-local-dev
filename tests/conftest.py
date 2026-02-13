"""Shared test fixtures for claude-local-dev."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def claude_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary Claude config directory and redirect config.py to it."""
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "plugins").mkdir()
    (claude / "plugins" / "marketplaces").mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude))
    return claude


@pytest.fixture
def populated_claude_dir(claude_dir: Path) -> Path:
    """A claude dir pre-populated with realistic existing data.

    Includes hooks in settings.json, an official marketplace,
    and an existing plugin from the official marketplace.
    """
    # settings.json with hooks (must be preserved)
    settings = {
        "autoUpdatesChannel": "latest",
        "enabledPlugins": {
            "plugin-dev@claude-plugins-official": True,
        },
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "bash guard.sh",
                            "timeout": 5000,
                        }
                    ],
                }
            ]
        },
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    # known_marketplaces.json with official marketplace
    marketplaces = {
        "claude-plugins-official": {
            "source": {
                "source": "github",
                "repo": "anthropics/claude-plugins-official",
            },
            "installLocation": str(
                claude_dir / "plugins" / "marketplaces" / "claude-plugins-official"
            ),
            "lastUpdated": "2026-01-01T00:00:00.000Z",
        }
    }
    (claude_dir / "plugins" / "known_marketplaces.json").write_text(
        json.dumps(marketplaces, indent=2)
    )

    # installed_plugins.json with official plugin
    installed = {
        "version": 2,
        "plugins": {
            "plugin-dev@claude-plugins-official": [
                {
                    "scope": "project",
                    "installPath": str(
                        claude_dir
                        / "plugins"
                        / "marketplaces"
                        / "claude-plugins-official"
                        / "plugin-dev"
                    ),
                    "version": "abc123",
                    "installedAt": "2026-01-01T00:00:00.000Z",
                    "lastUpdated": "2026-01-01T00:00:00.000Z",
                    "gitCommitSha": "abc123",
                    "projectPath": str(claude_dir.parent),
                }
            ]
        },
    }
    (claude_dir / "plugins" / "installed_plugins.json").write_text(
        json.dumps(installed, indent=2)
    )

    return claude_dir


@pytest.fixture
def mock_plugin(tmp_path: Path) -> Path:
    """Create a minimal valid plugin directory."""
    plugin_dir = tmp_path / "my-test-plugin"
    plugin_dir.mkdir()
    dot_claude = plugin_dir / ".claude-plugin"
    dot_claude.mkdir()
    plugin_json = {
        "name": "my-test-plugin",
        "version": "1.0.0",
        "description": "A test plugin",
    }
    (dot_claude / "plugin.json").write_text(json.dumps(plugin_json, indent=2))
    return plugin_dir
