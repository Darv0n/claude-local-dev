"""claude-local-dev init — create local-dev marketplace structure."""

from __future__ import annotations

import typer
from rich.console import Console

from claude_local_dev.cli import app
from claude_local_dev.config import get_local_dev_dir, get_local_dev_plugins_dir, get_marketplace_json_path
from claude_local_dev.registry import is_marketplace_registered, read_marketplace_manifest, register_marketplace, write_marketplace_manifest

console = Console()


@app.command()
def init() -> None:
    """Create the local-dev marketplace directory structure and register it."""
    plugins_dir = get_local_dev_plugins_dir()
    local_dev_dir = get_local_dev_dir()

    # Create directory structure
    plugins_dir.mkdir(parents=True, exist_ok=True)

    # Create marketplace.json if missing
    manifest_path = get_marketplace_json_path()
    if not manifest_path.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        write_marketplace_manifest(read_marketplace_manifest())
        console.print(f"  Manifest: {manifest_path}")

    # Register in known_marketplaces.json
    already_registered = is_marketplace_registered()
    register_marketplace()

    if already_registered:
        console.print(f"[yellow]Marketplace already registered.[/yellow] Updated entry.")
    else:
        console.print(f"[green]Marketplace registered:[/green] local-dev")

    console.print(f"  Directory: {local_dev_dir}")
    console.print(f"  Plugins:   {plugins_dir}")
