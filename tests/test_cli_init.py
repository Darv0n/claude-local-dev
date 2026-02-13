"""Tests for the init command."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from claude_local_dev.cli import app

runner = CliRunner()


def test_init_creates_structure(claude_dir: Path) -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Marketplace registered" in result.output

    plugins_dir = claude_dir / "plugins" / "marketplaces" / "local-dev" / "plugins"
    assert plugins_dir.exists()

    marketplaces = json.loads(
        (claude_dir / "plugins" / "known_marketplaces.json").read_text()
    )
    assert "local-dev" in marketplaces


def test_init_idempotent(claude_dir: Path) -> None:
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "already registered" in result.output


def test_init_preserves_existing_marketplaces(populated_claude_dir: Path) -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0

    marketplaces = json.loads(
        (populated_claude_dir / "plugins" / "known_marketplaces.json").read_text()
    )
    assert "claude-plugins-official" in marketplaces
    assert "local-dev" in marketplaces
