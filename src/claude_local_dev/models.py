"""Pydantic v2 models for the three JSON file schemas.

These model ONLY the structures we need to read/write.
settings.json is handled as raw dict (we only touch enabledPlugins).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


# --- installed_plugins.json ---

class PluginInstallRecord(BaseModel):
    """A single install record for a plugin."""
    scope: str = "project"
    install_path: str = Field(alias="installPath")
    version: str = "1.0.0"
    installed_at: str = Field(alias="installedAt")
    last_updated: str = Field(alias="lastUpdated")
    git_commit_sha: str | None = Field(default=None, alias="gitCommitSha")
    project_path: str = Field(alias="projectPath")

    model_config = {"populate_by_name": True}

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize using the camelCase aliases for JSON output."""
        d: dict[str, Any] = {
            "scope": self.scope,
            "installPath": self.install_path,
            "version": self.version,
            "installedAt": self.installed_at,
            "lastUpdated": self.last_updated,
            "projectPath": self.project_path,
        }
        if self.git_commit_sha is not None:
            d["gitCommitSha"] = self.git_commit_sha
        return d


class InstalledPluginsFile(BaseModel):
    """Top-level structure of installed_plugins.json."""
    version: int = 2
    plugins: dict[str, list[PluginInstallRecord]] = Field(default_factory=dict)


# --- known_marketplaces.json ---

class MarketplaceSource(BaseModel):
    """Source descriptor for a marketplace."""
    source: str  # "github" or "directory"
    repo: str | None = None
    path: str | None = None


class MarketplaceEntry(BaseModel):
    """A single marketplace entry."""
    source: MarketplaceSource
    install_location: str = Field(alias="installLocation")
    last_updated: str = Field(alias="lastUpdated")

    model_config = {"populate_by_name": True}

    def to_json_dict(self) -> dict[str, Any]:
        source_dict: dict[str, Any] = {"source": self.source.source}
        if self.source.repo is not None:
            source_dict["repo"] = self.source.repo
        if self.source.path is not None:
            source_dict["path"] = self.source.path
        return {
            "source": source_dict,
            "installLocation": self.install_location,
            "lastUpdated": self.last_updated,
        }


# --- Factory helpers ---

def make_install_record(
    plugin_name: str,
    install_path: str,
    version: str = "1.0.0",
    project_path: str | None = None,
) -> PluginInstallRecord:
    """Create a new PluginInstallRecord with current timestamp."""
    from pathlib import Path
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if project_path is None:
        project_path = str(Path.home())
    return PluginInstallRecord(
        scope="project",
        installPath=install_path,
        version=version,
        installedAt=now,
        lastUpdated=now,
        projectPath=project_path,
    )


def make_local_dev_marketplace(install_location: str) -> MarketplaceEntry:
    """Create a MarketplaceEntry for the local-dev marketplace."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return MarketplaceEntry(
        source=MarketplaceSource(source="directory", path=install_location),
        installLocation=install_location,
        lastUpdated=now,
    )
