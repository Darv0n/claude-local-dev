"""Tests for config.py — path resolution and env var override."""

from __future__ import annotations

from pathlib import Path

from claude_local_dev.config import (
    get_claude_config_dir,
    get_installed_plugins_path,
    get_known_marketplaces_path,
    get_local_dev_dir,
    get_local_dev_plugins_dir,
    get_plugins_dir,
    get_settings_path,
    MARKETPLACE_NAME,
)


def test_env_override(claude_dir: Path) -> None:
    assert get_claude_config_dir() == claude_dir


def test_default_falls_back_to_home(monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    assert get_claude_config_dir() == Path.home() / ".claude"


def test_path_hierarchy(claude_dir: Path) -> None:
    assert get_plugins_dir() == claude_dir / "plugins"
    assert get_local_dev_dir() == claude_dir / "plugins" / "marketplaces" / "local-dev"
    assert get_local_dev_plugins_dir() == (
        claude_dir / "plugins" / "marketplaces" / "local-dev" / "plugins"
    )


def test_json_paths(claude_dir: Path) -> None:
    assert get_settings_path() == claude_dir / "settings.json"
    assert get_installed_plugins_path() == claude_dir / "plugins" / "installed_plugins.json"
    assert get_known_marketplaces_path() == claude_dir / "plugins" / "known_marketplaces.json"


def test_marketplace_name() -> None:
    assert MARKETPLACE_NAME == "local-dev"
