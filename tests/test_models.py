"""Tests for models.py — Pydantic schema validation."""

from __future__ import annotations

from claude_local_dev.models import (
    InstalledPluginsFile,
    MarketplaceEntry,
    MarketplaceSource,
    PluginInstallRecord,
    make_install_record,
    make_local_dev_marketplace,
)


def test_plugin_install_record_roundtrip() -> None:
    record = PluginInstallRecord(
        scope="project",
        installPath="C:/test/path",
        version="1.0.0",
        installedAt="2026-01-01T00:00:00.000Z",
        lastUpdated="2026-01-01T00:00:00.000Z",
        projectPath="C:/home",
    )
    d = record.to_json_dict()
    assert d["installPath"] == "C:/test/path"
    assert d["version"] == "1.0.0"
    assert "gitCommitSha" not in d


def test_plugin_install_record_with_sha() -> None:
    record = PluginInstallRecord(
        scope="project",
        installPath="/test",
        version="abc",
        installedAt="2026-01-01T00:00:00.000Z",
        lastUpdated="2026-01-01T00:00:00.000Z",
        gitCommitSha="abc123",
        projectPath="/home",
    )
    d = record.to_json_dict()
    assert d["gitCommitSha"] == "abc123"


def test_installed_plugins_file_defaults() -> None:
    f = InstalledPluginsFile()
    assert f.version == 2
    assert f.plugins == {}


def test_marketplace_entry_roundtrip() -> None:
    entry = MarketplaceEntry(
        source=MarketplaceSource(source="directory", path="/test"),
        installLocation="/test",
        lastUpdated="2026-01-01T00:00:00.000Z",
    )
    d = entry.to_json_dict()
    assert d["source"]["source"] == "directory"
    assert d["source"]["path"] == "/test"
    assert "repo" not in d["source"]
    assert d["installLocation"] == "/test"


def test_marketplace_entry_github() -> None:
    entry = MarketplaceEntry(
        source=MarketplaceSource(source="github", repo="org/repo"),
        installLocation="/somewhere",
        lastUpdated="2026-01-01T00:00:00.000Z",
    )
    d = entry.to_json_dict()
    assert d["source"]["repo"] == "org/repo"
    assert "path" not in d["source"]


def test_make_install_record() -> None:
    record = make_install_record(
        plugin_name="test",
        install_path="/plugins/test",
        version="2.0.0",
        project_path="/home/user",
    )
    assert record.install_path == "/plugins/test"
    assert record.version == "2.0.0"
    assert record.project_path == "/home/user"
    assert record.installed_at == record.last_updated


def test_make_local_dev_marketplace() -> None:
    entry = make_local_dev_marketplace("/my/path")
    assert entry.source.source == "directory"
    assert entry.source.path == "/my/path"
    assert entry.install_location == "/my/path"
