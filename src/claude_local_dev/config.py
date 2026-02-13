"""Path constants and platform detection.

All file paths flow from CLAUDE_CONFIG_DIR, which defaults to ~/.claude
but can be overridden via environment variable for testing.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"


def get_claude_config_dir() -> Path:
    """Return the Claude configuration directory.

    Checks CLAUDE_CONFIG_DIR env var first (for test isolation),
    then falls back to ~/.claude.
    """
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude"


def get_plugins_dir() -> Path:
    return get_claude_config_dir() / "plugins"


def get_marketplaces_dir() -> Path:
    return get_plugins_dir() / "marketplaces"


def get_local_dev_dir() -> Path:
    return get_marketplaces_dir() / "local-dev"


def get_local_dev_plugins_dir() -> Path:
    return get_local_dev_dir() / "plugins"


# JSON file paths

def get_settings_path() -> Path:
    return get_claude_config_dir() / "settings.json"


def get_installed_plugins_path() -> Path:
    return get_plugins_dir() / "installed_plugins.json"


def get_known_marketplaces_path() -> Path:
    return get_plugins_dir() / "known_marketplaces.json"


MARKETPLACE_NAME = "local-dev"
