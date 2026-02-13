"""Tests for the add command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from claude_local_dev.cli import app
from claude_local_dev.junction import is_link

runner = CliRunner()


def _init_marketplace(claude_dir: Path) -> None:
    """Helper: run init first so add can work."""
    runner.invoke(app, ["init"])


def test_add_registers_plugin(
    populated_claude_dir: Path, mock_plugin: Path
) -> None:
    _init_marketplace(populated_claude_dir)
    result = runner.invoke(app, ["add", str(mock_plugin)])
    assert result.exit_code == 0
    assert "Plugin registered" in result.output

    # Junction created
    link = (
        populated_claude_dir
        / "plugins"
        / "marketplaces"
        / "local-dev"
        / "plugins"
        / "my-test-plugin"
    )
    assert is_link(link)

    # installed_plugins.json updated
    installed = json.loads(
        (populated_claude_dir / "plugins" / "installed_plugins.json").read_text()
    )
    assert "my-test-plugin@local-dev" in installed["plugins"]
    # Official plugin still there
    assert "plugin-dev@claude-plugins-official" in installed["plugins"]

    # settings.json updated with hooks preserved
    settings = json.loads(
        (populated_claude_dir / "settings.json").read_text()
    )
    assert settings["enabledPlugins"]["my-test-plugin@local-dev"] is True
    assert "hooks" in settings


def test_add_fails_without_init(claude_dir: Path, mock_plugin: Path) -> None:
    result = runner.invoke(app, ["add", str(mock_plugin)])
    assert result.exit_code == 1
    assert "not initialized" in result.output


def test_add_fails_for_invalid_plugin(populated_claude_dir: Path, tmp_path: Path) -> None:
    _init_marketplace(populated_claude_dir)
    bad_dir = tmp_path / "not-a-plugin"
    bad_dir.mkdir()
    result = runner.invoke(app, ["add", str(bad_dir)])
    assert result.exit_code == 1
    assert "Not a valid plugin" in result.output


def test_add_idempotent(populated_claude_dir: Path, mock_plugin: Path) -> None:
    _init_marketplace(populated_claude_dir)
    runner.invoke(app, ["add", str(mock_plugin)])
    result = runner.invoke(app, ["add", str(mock_plugin)])
    assert result.exit_code == 0
    assert "already registered" in result.output


def test_add_rejects_bad_plugin_name(
    populated_claude_dir: Path, tmp_path: Path
) -> None:
    """GAP 6: Plugin names with slashes or dots-first are rejected."""
    _init_marketplace(populated_claude_dir)
    bad_plugin = tmp_path / ".hidden-plugin"
    bad_plugin.mkdir()
    (bad_plugin / ".claude-plugin").mkdir()
    (bad_plugin / ".claude-plugin" / "plugin.json").write_text(
        '{"name": "../escape-attempt"}'
    )
    result = runner.invoke(app, ["add", str(bad_plugin)])
    assert result.exit_code == 1
    assert "Invalid plugin name" in result.output
