"""Tests for the verify command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from claude_local_dev.cli import app
from claude_local_dev.config import get_local_dev_plugins_dir
from claude_local_dev.registry import (
    add_installed_plugin,
    enable_plugin,
)

runner = CliRunner()


def test_verify_clean_state(populated_claude_dir: Path, mock_plugin: Path) -> None:
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", str(mock_plugin)])

    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_verify_detects_missing_junction(populated_claude_dir: Path) -> None:
    runner.invoke(app, ["init"])
    # Add to registry but don't create junction
    add_installed_plugin("ghost-plugin", "/nonexistent")
    enable_plugin("ghost-plugin")

    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 1
    assert "ghost-plugin" in result.output
    assert "no junction" in result.output


def test_verify_detects_enabled_not_installed(
    populated_claude_dir: Path,
) -> None:
    runner.invoke(app, ["init"])
    enable_plugin("orphan")

    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 1
    assert "orphan" in result.output
    assert "missing from installed_plugins.json" in result.output


def test_verify_no_marketplace(claude_dir: Path) -> None:
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 1
    assert "not registered" in result.output


def test_verify_empty_marketplace(claude_dir: Path) -> None:
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "0 plugin(s)" in result.output
