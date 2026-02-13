"""Tests for the remove command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from claude_local_dev.cli import app
from claude_local_dev.junction import is_link

runner = CliRunner()


def _setup_plugin(claude_dir: Path, mock_plugin: Path) -> None:
    """Init marketplace and add a plugin."""
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", str(mock_plugin)])


def test_remove_cleans_everything(
    populated_claude_dir: Path, mock_plugin: Path
) -> None:
    _setup_plugin(populated_claude_dir, mock_plugin)

    result = runner.invoke(app, ["remove", "my-test-plugin"])
    assert result.exit_code == 0
    assert "Plugin removed" in result.output

    # Junction gone
    link = (
        populated_claude_dir
        / "plugins"
        / "marketplaces"
        / "local-dev"
        / "plugins"
        / "my-test-plugin"
    )
    assert not is_link(link)
    assert not link.exists()

    # Removed from installed_plugins.json
    installed = json.loads(
        (populated_claude_dir / "plugins" / "installed_plugins.json").read_text()
    )
    assert "my-test-plugin@local-dev" not in installed["plugins"]
    # Official plugin still there
    assert "plugin-dev@claude-plugins-official" in installed["plugins"]

    # Removed from settings.json, hooks preserved
    settings = json.loads(
        (populated_claude_dir / "settings.json").read_text()
    )
    assert "my-test-plugin@local-dev" not in settings["enabledPlugins"]
    assert "hooks" in settings


def test_remove_nonexistent_plugin(populated_claude_dir: Path) -> None:
    result = runner.invoke(app, ["remove", "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output
