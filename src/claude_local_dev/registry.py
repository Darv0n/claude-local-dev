"""Read-modify-write operations for all three JSON registry files.

Critical constraint: NEVER drop unknown keys. We only touch the keys
we own (local-dev marketplace entries, our plugin entries, our enabledPlugins
entries). Everything else passes through untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import re

from claude_local_dev.config import (
    MARKETPLACE_NAME,
    get_installed_plugins_path,
    get_known_marketplaces_path,
    get_local_dev_dir,
    get_local_dev_plugins_dir,
    get_settings_path,
)
from claude_local_dev.errors import RegistryCorrupted
from claude_local_dev.models import (
    make_install_record,
    make_local_dev_marketplace,
)

# Plugin names must be safe for filesystem use and registry keys
_VALID_PLUGIN_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def _read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file, returning empty dict if missing or empty."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RegistryCorrupted(f"{path}: {e}") from e


def _write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a JSON file with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_plugin_name(name: str) -> None:
    """Validate a plugin name is safe for filesystem and registry use."""
    if not name:
        raise ValueError("Plugin name cannot be empty")
    if not _VALID_PLUGIN_NAME.match(name):
        raise ValueError(
            f"Invalid plugin name: {name!r} "
            f"(must match {_VALID_PLUGIN_NAME.pattern})"
        )


def _plugin_key(plugin_name: str) -> str:
    """Build the composite key: name@local-dev."""
    return f"{plugin_name}@{MARKETPLACE_NAME}"


# --- settings.json ---


def read_settings() -> dict[str, Any]:
    return _read_json(get_settings_path())


def write_settings(data: dict[str, Any]) -> None:
    _write_json(get_settings_path(), data)


def enable_plugin(plugin_name: str) -> None:
    """Add plugin to enabledPlugins in settings.json. Preserves all other keys."""
    data = read_settings()
    enabled = data.setdefault("enabledPlugins", {})
    enabled[_plugin_key(plugin_name)] = True
    write_settings(data)


def disable_plugin(plugin_name: str) -> None:
    """Remove plugin from enabledPlugins in settings.json. Preserves all other keys."""
    data = read_settings()
    enabled = data.get("enabledPlugins", {})
    key = _plugin_key(plugin_name)
    if key in enabled:
        del enabled[key]
    write_settings(data)


def is_plugin_enabled(plugin_name: str) -> bool:
    data = read_settings()
    return data.get("enabledPlugins", {}).get(_plugin_key(plugin_name), False)


def list_enabled_local_dev_plugins() -> list[str]:
    """Return names of all local-dev plugins that are enabled."""
    data = read_settings()
    enabled = data.get("enabledPlugins", {})
    suffix = f"@{MARKETPLACE_NAME}"
    return [
        key.removesuffix(suffix)
        for key in enabled
        if key.endswith(suffix) and enabled[key]
    ]


# --- installed_plugins.json ---


def read_installed_plugins() -> dict[str, Any]:
    return _read_json(get_installed_plugins_path())


def write_installed_plugins(data: dict[str, Any]) -> None:
    _write_json(get_installed_plugins_path(), data)


def add_installed_plugin(
    plugin_name: str,
    install_path: str,
    version: str = "1.0.0",
    project_path: str | None = None,
) -> None:
    """Add a plugin install record. Preserves all other plugins."""
    data = read_installed_plugins()
    data.setdefault("version", 2)
    plugins = data.setdefault("plugins", {})
    key = _plugin_key(plugin_name)
    record = make_install_record(
        plugin_name=plugin_name,
        install_path=install_path,
        version=version,
        project_path=project_path,
    )
    plugins[key] = [record.to_json_dict()]
    write_installed_plugins(data)


def remove_installed_plugin(plugin_name: str) -> None:
    """Remove a plugin's install records. Preserves all other plugins."""
    data = read_installed_plugins()
    plugins = data.get("plugins", {})
    key = _plugin_key(plugin_name)
    if key in plugins:
        del plugins[key]
    write_installed_plugins(data)


def get_installed_plugin(plugin_name: str) -> list[dict[str, Any]] | None:
    """Get install records for a plugin, or None if not installed."""
    data = read_installed_plugins()
    return data.get("plugins", {}).get(_plugin_key(plugin_name))


def list_installed_local_dev_plugins() -> dict[str, list[dict[str, Any]]]:
    """Return all local-dev plugin install records."""
    data = read_installed_plugins()
    plugins = data.get("plugins", {})
    suffix = f"@{MARKETPLACE_NAME}"
    return {
        key.removesuffix(suffix): records
        for key, records in plugins.items()
        if key.endswith(suffix)
    }


# --- known_marketplaces.json ---


def read_known_marketplaces() -> dict[str, Any]:
    return _read_json(get_known_marketplaces_path())


def write_known_marketplaces(data: dict[str, Any]) -> None:
    _write_json(get_known_marketplaces_path(), data)


def register_marketplace() -> None:
    """Register the local-dev marketplace. Preserves all other marketplaces."""
    data = read_known_marketplaces()
    install_location = str(get_local_dev_dir())
    entry = make_local_dev_marketplace(install_location)
    data[MARKETPLACE_NAME] = entry.to_json_dict()
    write_known_marketplaces(data)


def unregister_marketplace() -> None:
    """Remove the local-dev marketplace entry. Preserves all other marketplaces."""
    data = read_known_marketplaces()
    if MARKETPLACE_NAME in data:
        del data[MARKETPLACE_NAME]
    write_known_marketplaces(data)


def is_marketplace_registered() -> bool:
    data = read_known_marketplaces()
    return MARKETPLACE_NAME in data


# --- Plugin metadata reading ---


def read_plugin_json(plugin_path: Path) -> dict[str, Any]:
    """Read the plugin.json from a plugin directory."""
    pj = plugin_path / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        return {}
    return json.loads(pj.read_text(encoding="utf-8"))


def get_plugin_name(plugin_path: Path) -> str:
    """Extract the plugin name from its plugin.json, falling back to dir name."""
    meta = read_plugin_json(plugin_path)
    return meta.get("name") or plugin_path.name


def get_plugin_version(plugin_path: Path) -> str:
    """Extract the version from plugin.json, defaulting to 1.0.0."""
    meta = read_plugin_json(plugin_path)
    return meta.get("version", "1.0.0")
