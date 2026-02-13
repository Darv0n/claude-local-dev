"""Cross-platform filesystem link operations.

Windows: NTFS junctions (via mklink /J) — no admin rights needed.
Unix: Symlinks (os.symlink).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from claude_local_dev.config import IS_WINDOWS
from claude_local_dev.errors import BrokenJunction, JunctionError


def create_link(link_path: Path, target_path: Path) -> None:
    """Create a junction (Windows) or symlink (Unix) pointing link_path -> target_path.

    Raises JunctionError if the operation fails.
    """
    target_path = target_path.resolve()
    if not target_path.exists():
        raise JunctionError(f"Target does not exist: {target_path}")

    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.exists() or link_path.is_symlink():
        # If it already points to the right place, we're done
        try:
            if link_path.resolve() == target_path:
                return
        except OSError:
            pass
        raise JunctionError(f"Link path already exists: {link_path}")

    if IS_WINDOWS:
        _create_junction_windows(link_path, target_path)
    else:
        _create_symlink_unix(link_path, target_path)


def remove_link(link_path: Path) -> None:
    """Remove a junction or symlink. Does nothing if it doesn't exist."""
    if not link_path.exists() and not link_path.is_symlink():
        return

    if IS_WINDOWS:
        _remove_junction_windows(link_path)
    else:
        _remove_symlink_unix(link_path)


def is_link(path: Path) -> bool:
    """Check if a path is a junction (Windows) or symlink."""
    if not path.exists() and not path.is_symlink():
        return False
    if IS_WINDOWS:
        return _is_junction_windows(path)
    return path.is_symlink()


def link_target(path: Path) -> Path | None:
    """Return the target of a junction/symlink, or None."""
    try:
        return Path(os.readlink(path))
    except OSError:
        return None


def is_link_healthy(path: Path) -> bool:
    """Check if a junction/symlink exists and its target is accessible."""
    if not is_link(path):
        return False
    target = link_target(path)
    if target is None:
        return False
    return target.exists()


# --- Windows: NTFS Junctions ---


def _create_junction_windows(link_path: Path, target_path: Path) -> None:
    try:
        # Python 3.12+ on Windows: os.symlink for directories
        # creates a junction-like structure. But mklink /J is more reliable
        # for NTFS junctions specifically.
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise JunctionError(
                f"mklink /J failed: {result.stderr.strip() or result.stdout.strip()}"
            )
    except FileNotFoundError:
        raise JunctionError("cmd.exe not found — cannot create NTFS junction")


def _remove_junction_windows(link_path: Path) -> None:
    try:
        # Junctions on Windows are directories; rmdir removes the link
        # without affecting the target
        result = subprocess.run(
            ["cmd", "/c", "rmdir", str(link_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise JunctionError(
                f"rmdir failed: {result.stderr.strip() or result.stdout.strip()}"
            )
    except FileNotFoundError:
        raise JunctionError("cmd.exe not found — cannot remove junction")


def _is_junction_windows(path: Path) -> bool:
    """Check if path is an NTFS junction or symlink."""
    try:
        # os.readlink works for both junctions and symlinks on Windows
        os.readlink(path)
        return True
    except OSError:
        return False


# --- Unix: Symlinks ---


def _create_symlink_unix(link_path: Path, target_path: Path) -> None:
    try:
        os.symlink(target_path, link_path, target_is_directory=True)
    except OSError as e:
        raise JunctionError(f"symlink failed: {e}") from e


def _remove_symlink_unix(link_path: Path) -> None:
    try:
        os.unlink(link_path)
    except OSError as e:
        raise JunctionError(f"unlink failed: {e}") from e
