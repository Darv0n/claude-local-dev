"""Tests for registry.py — the critical data preservation tests.

Every test here verifies that operations on local-dev data
do NOT corrupt or drop data belonging to other plugins/marketplaces.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_local_dev import registry
from claude_local_dev.errors import RegistryCorrupted


# --- settings.json ---


class TestSettingsPreservation:
    """Operations on enabledPlugins must preserve hooks and other keys."""

    def test_enable_plugin_preserves_hooks(self, populated_claude_dir: Path) -> None:
        registry.enable_plugin("my-plugin")

        data = json.loads((populated_claude_dir / "settings.json").read_text())
        # Hooks must still be there
        assert "hooks" in data
        assert data["hooks"]["PreToolUse"][0]["matcher"] == "Bash"
        # Our plugin must be enabled
        assert data["enabledPlugins"]["my-plugin@local-dev"] is True
        # Official plugin must still be enabled
        assert data["enabledPlugins"]["plugin-dev@claude-plugins-official"] is True

    def test_enable_plugin_preserves_auto_updates(
        self, populated_claude_dir: Path
    ) -> None:
        registry.enable_plugin("test")
        data = json.loads((populated_claude_dir / "settings.json").read_text())
        assert data["autoUpdatesChannel"] == "latest"

    def test_disable_plugin_preserves_hooks(self, populated_claude_dir: Path) -> None:
        registry.enable_plugin("my-plugin")
        registry.disable_plugin("my-plugin")

        data = json.loads((populated_claude_dir / "settings.json").read_text())
        assert "hooks" in data
        assert "my-plugin@local-dev" not in data["enabledPlugins"]
        assert data["enabledPlugins"]["plugin-dev@claude-plugins-official"] is True

    def test_disable_nonexistent_is_safe(self, populated_claude_dir: Path) -> None:
        registry.disable_plugin("nonexistent")
        data = json.loads((populated_claude_dir / "settings.json").read_text())
        assert "hooks" in data

    def test_enable_creates_file_if_missing(self, claude_dir: Path) -> None:
        registry.enable_plugin("my-plugin")
        data = json.loads((claude_dir / "settings.json").read_text())
        assert data["enabledPlugins"]["my-plugin@local-dev"] is True

    def test_is_plugin_enabled(self, claude_dir: Path) -> None:
        assert registry.is_plugin_enabled("x") is False
        registry.enable_plugin("x")
        assert registry.is_plugin_enabled("x") is True

    def test_list_enabled_local_dev_plugins(self, populated_claude_dir: Path) -> None:
        registry.enable_plugin("a")
        registry.enable_plugin("b")
        names = registry.list_enabled_local_dev_plugins()
        assert sorted(names) == ["a", "b"]


# --- installed_plugins.json ---


class TestInstalledPluginsPreservation:
    """Operations on local-dev plugins must preserve official plugin records."""

    def test_add_preserves_official_plugins(self, populated_claude_dir: Path) -> None:
        registry.add_installed_plugin("my-plugin", "/install/my-plugin")

        data = json.loads(
            (populated_claude_dir / "plugins" / "installed_plugins.json").read_text()
        )
        # Official plugin still there
        assert "plugin-dev@claude-plugins-official" in data["plugins"]
        official = data["plugins"]["plugin-dev@claude-plugins-official"][0]
        assert official["gitCommitSha"] == "abc123"
        # Our plugin added
        assert "my-plugin@local-dev" in data["plugins"]

    def test_add_preserves_version_field(self, populated_claude_dir: Path) -> None:
        registry.add_installed_plugin("my-plugin", "/install/my-plugin")
        data = json.loads(
            (populated_claude_dir / "plugins" / "installed_plugins.json").read_text()
        )
        assert data["version"] == 2

    def test_remove_preserves_official_plugins(
        self, populated_claude_dir: Path
    ) -> None:
        registry.add_installed_plugin("my-plugin", "/install/my-plugin")
        registry.remove_installed_plugin("my-plugin")

        data = json.loads(
            (populated_claude_dir / "plugins" / "installed_plugins.json").read_text()
        )
        assert "plugin-dev@claude-plugins-official" in data["plugins"]
        assert "my-plugin@local-dev" not in data["plugins"]

    def test_remove_nonexistent_is_safe(self, populated_claude_dir: Path) -> None:
        registry.remove_installed_plugin("nonexistent")
        data = json.loads(
            (populated_claude_dir / "plugins" / "installed_plugins.json").read_text()
        )
        assert "plugin-dev@claude-plugins-official" in data["plugins"]

    def test_idempotent_add(self, claude_dir: Path) -> None:
        registry.add_installed_plugin("x", "/path/x")
        registry.add_installed_plugin("x", "/path/x")
        data = json.loads(
            (claude_dir / "plugins" / "installed_plugins.json").read_text()
        )
        # Still just one record list
        assert len(data["plugins"]["x@local-dev"]) == 1

    def test_creates_file_if_missing(self, claude_dir: Path) -> None:
        registry.add_installed_plugin("x", "/path")
        data = json.loads(
            (claude_dir / "plugins" / "installed_plugins.json").read_text()
        )
        assert data["version"] == 2
        assert "x@local-dev" in data["plugins"]

    def test_get_installed_plugin(self, claude_dir: Path) -> None:
        assert registry.get_installed_plugin("x") is None
        registry.add_installed_plugin("x", "/path")
        records = registry.get_installed_plugin("x")
        assert records is not None
        assert records[0]["installPath"] == "/path"

    def test_list_installed_local_dev_plugins(
        self, populated_claude_dir: Path
    ) -> None:
        registry.add_installed_plugin("a", "/a")
        registry.add_installed_plugin("b", "/b")
        plugins = registry.list_installed_local_dev_plugins()
        assert sorted(plugins.keys()) == ["a", "b"]


# --- known_marketplaces.json ---


class TestMarketplacePreservation:
    """Operations on local-dev must preserve official marketplace entries."""

    def test_register_preserves_official(self, populated_claude_dir: Path) -> None:
        registry.register_marketplace()

        data = json.loads(
            (
                populated_claude_dir / "plugins" / "known_marketplaces.json"
            ).read_text()
        )
        assert "claude-plugins-official" in data
        assert data["claude-plugins-official"]["source"]["repo"] == (
            "anthropics/claude-plugins-official"
        )
        assert "local-dev" in data

    def test_unregister_preserves_official(self, populated_claude_dir: Path) -> None:
        registry.register_marketplace()
        registry.unregister_marketplace()

        data = json.loads(
            (
                populated_claude_dir / "plugins" / "known_marketplaces.json"
            ).read_text()
        )
        assert "claude-plugins-official" in data
        assert "local-dev" not in data

    def test_register_idempotent(self, claude_dir: Path) -> None:
        registry.register_marketplace()
        registry.register_marketplace()
        data = json.loads(
            (claude_dir / "plugins" / "known_marketplaces.json").read_text()
        )
        assert "local-dev" in data

    def test_is_marketplace_registered(self, claude_dir: Path) -> None:
        assert registry.is_marketplace_registered() is False
        registry.register_marketplace()
        assert registry.is_marketplace_registered() is True

    def test_creates_file_if_missing(self, claude_dir: Path) -> None:
        registry.register_marketplace()
        data = json.loads(
            (claude_dir / "plugins" / "known_marketplaces.json").read_text()
        )
        assert data["local-dev"]["source"]["source"] == "directory"


# --- Plugin metadata ---


class TestPluginMetadata:
    def test_read_plugin_json(self, mock_plugin: Path) -> None:
        meta = registry.read_plugin_json(mock_plugin)
        assert meta["name"] == "my-test-plugin"

    def test_read_missing_plugin_json(self, tmp_path: Path) -> None:
        meta = registry.read_plugin_json(tmp_path / "nonexistent")
        assert meta == {}

    def test_get_plugin_name(self, mock_plugin: Path) -> None:
        assert registry.get_plugin_name(mock_plugin) == "my-test-plugin"

    def test_get_plugin_name_falls_back_to_dirname(self, tmp_path: Path) -> None:
        d = tmp_path / "fallback-name"
        d.mkdir()
        (d / ".claude-plugin").mkdir()
        (d / ".claude-plugin" / "plugin.json").write_text("{}")
        assert registry.get_plugin_name(d) == "fallback-name"

    def test_get_plugin_version(self, mock_plugin: Path) -> None:
        assert registry.get_plugin_version(mock_plugin) == "1.0.0"

    def test_get_plugin_version_default(self, tmp_path: Path) -> None:
        assert registry.get_plugin_version(tmp_path) == "1.0.0"


# --- GAP fixes ---


class TestCorruptedJsonHandling:
    """GAP 3: Corrupt JSON files raise RegistryCorrupted, not JSONDecodeError."""

    def test_corrupted_settings_raises(self, claude_dir: Path) -> None:
        (claude_dir / "settings.json").write_text("{bad json!!!")
        with pytest.raises(RegistryCorrupted, match="settings.json"):
            registry.read_settings()

    def test_corrupted_installed_plugins_raises(self, claude_dir: Path) -> None:
        (claude_dir / "plugins" / "installed_plugins.json").write_text("not json")
        with pytest.raises(RegistryCorrupted, match="installed_plugins.json"):
            registry.read_installed_plugins()

    def test_corrupted_marketplaces_raises(self, claude_dir: Path) -> None:
        (claude_dir / "plugins" / "known_marketplaces.json").write_text("[1,2,")
        with pytest.raises(RegistryCorrupted, match="known_marketplaces.json"):
            registry.read_known_marketplaces()


class TestPluginNameValidation:
    """GAP 6: Plugin names must be filesystem-safe."""

    def test_valid_names(self) -> None:
        for name in ["my-plugin", "plugin_v2", "Plugin.Test", "a123"]:
            registry.validate_plugin_name(name)  # Should not raise

    def test_empty_name(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            registry.validate_plugin_name("")

    def test_slash_in_name(self) -> None:
        with pytest.raises(ValueError, match="Invalid plugin name"):
            registry.validate_plugin_name("foo/bar")

    def test_starts_with_dot(self) -> None:
        with pytest.raises(ValueError, match="Invalid plugin name"):
            registry.validate_plugin_name(".hidden")

    def test_starts_with_dash(self) -> None:
        with pytest.raises(ValueError, match="Invalid plugin name"):
            registry.validate_plugin_name("-bad")
