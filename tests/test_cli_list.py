"""Tests for the list command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claude_local_dev.cli import app

runner = CliRunner()


def test_list_empty(claude_dir: Path) -> None:
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No local-dev plugins" in result.output


def test_list_shows_plugin(populated_claude_dir: Path, mock_plugin: Path) -> None:
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", str(mock_plugin)])

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "my-test-plugin" in result.output


def test_list_fails_without_init(claude_dir: Path) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 1
    assert "not initialized" in result.output
