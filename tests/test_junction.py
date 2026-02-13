"""Tests for junction.py — platform-conditional link operations."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from claude_local_dev.junction import (
    create_link,
    is_link,
    is_link_healthy,
    link_target,
    remove_link,
)
from claude_local_dev.errors import JunctionError


@pytest.fixture
def target_dir(tmp_path: Path) -> Path:
    """A real directory to serve as a link target."""
    d = tmp_path / "target"
    d.mkdir()
    (d / "marker.txt").write_text("exists")
    return d


@pytest.fixture
def link_path(tmp_path: Path) -> Path:
    """A path where a link should be created (does not exist yet)."""
    return tmp_path / "links" / "my-link"


class TestCreateLink:
    def test_creates_link(self, link_path: Path, target_dir: Path) -> None:
        create_link(link_path, target_dir)
        assert link_path.exists()
        assert (link_path / "marker.txt").read_text() == "exists"

    def test_creates_parent_dirs(self, link_path: Path, target_dir: Path) -> None:
        create_link(link_path, target_dir)
        assert link_path.parent.exists()

    def test_idempotent_same_target(
        self, link_path: Path, target_dir: Path
    ) -> None:
        create_link(link_path, target_dir)
        # Calling again with same target should not raise
        create_link(link_path, target_dir)
        assert is_link(link_path)

    def test_rejects_nonexistent_target(self, link_path: Path, tmp_path: Path) -> None:
        with pytest.raises(JunctionError, match="Target does not exist"):
            create_link(link_path, tmp_path / "nope")

    def test_rejects_existing_different_target(
        self, link_path: Path, target_dir: Path, tmp_path: Path
    ) -> None:
        create_link(link_path, target_dir)
        other = tmp_path / "other"
        other.mkdir()
        with pytest.raises(JunctionError, match="already exists"):
            create_link(link_path, other)


class TestRemoveLink:
    def test_removes_link(self, link_path: Path, target_dir: Path) -> None:
        create_link(link_path, target_dir)
        remove_link(link_path)
        assert not link_path.exists()
        # Target must still exist
        assert target_dir.exists()
        assert (target_dir / "marker.txt").exists()

    def test_noop_if_missing(self, link_path: Path) -> None:
        # Should not raise
        remove_link(link_path)


class TestIsLink:
    def test_true_for_link(self, link_path: Path, target_dir: Path) -> None:
        create_link(link_path, target_dir)
        assert is_link(link_path) is True

    def test_false_for_regular_dir(self, target_dir: Path) -> None:
        assert is_link(target_dir) is False

    def test_false_for_missing(self, tmp_path: Path) -> None:
        assert is_link(tmp_path / "missing") is False


class TestLinkTarget:
    def test_returns_target(self, link_path: Path, target_dir: Path) -> None:
        create_link(link_path, target_dir)
        target = link_target(link_path)
        assert target is not None
        # Windows junctions may have \\?\ prefix; normalize by comparing str paths
        def _normalize(p: Path) -> str:
            s = str(p.resolve())
            # Strip Windows extended-length path prefix
            for prefix in ("\\\\?\\", "//?/"):
                if s.startswith(prefix):
                    s = s[len(prefix):]
            return s.lower()
        assert _normalize(target) == _normalize(target_dir)

    def test_returns_none_for_regular_dir(self, target_dir: Path) -> None:
        assert link_target(target_dir) is None


class TestIsLinkHealthy:
    def test_healthy_link(self, link_path: Path, target_dir: Path) -> None:
        create_link(link_path, target_dir)
        assert is_link_healthy(link_path) is True

    def test_unhealthy_missing_path(self, tmp_path: Path) -> None:
        assert is_link_healthy(tmp_path / "missing") is False
