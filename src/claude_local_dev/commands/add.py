"""claude-local-dev add — register a plugin from a local directory."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from claude_local_dev.cli import app
from claude_local_dev.config import get_local_dev_cache_dir, get_local_dev_plugins_dir
from claude_local_dev.errors import JunctionError
from claude_local_dev.junction import create_link, is_link, remove_link
from claude_local_dev.registry import (
    add_installed_plugin,
    add_marketplace_plugin,
    enable_plugin,
    get_plugin_name,
    get_plugin_version,
    is_marketplace_registered,
    read_plugin_json,
    validate_plugin_name,
)

console = Console()


@app.command()
def add(
    plugin_path: Path = typer.Argument(
        ...,
        help="Path to the plugin directory (must contain .claude-plugin/plugin.json).",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
) -> None:
    """Register a local plugin: create junction, update registry, enable."""
    # Validate marketplace exists
    if not is_marketplace_registered():
        console.print(
            "[red]Marketplace not initialized.[/red] Run `claude-local-dev init` first."
        )
        raise typer.Exit(code=1)

    # Validate plugin structure
    plugin_json_path = plugin_path / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        console.print(
            f"[red]Not a valid plugin:[/red] {plugin_path}\n"
            f"  Missing .claude-plugin/plugin.json"
        )
        raise typer.Exit(code=1)

    plugin_meta = read_plugin_json(plugin_path)
    plugin_name = plugin_meta.get("name") or plugin_path.name
    plugin_version = plugin_meta.get("version", "1.0.0")
    plugin_description = plugin_meta.get("description", "")
    plugin_author = plugin_meta.get("author", {}).get("name", "")

    # Validate plugin name is filesystem-safe
    try:
        validate_plugin_name(plugin_name)
    except ValueError as e:
        console.print(f"[red]Invalid plugin name:[/red] {e}")
        raise typer.Exit(code=1)

    plugins_dir = get_local_dev_plugins_dir()
    link_path = plugins_dir / plugin_name

    # Compute cache path — this is where Claude Code actually loads from
    cache_dir = get_local_dev_cache_dir() / plugin_name
    cache_version_path = cache_dir / plugin_version

    # Check if already registered
    if is_link(link_path):
        console.print(
            f"[yellow]Plugin already registered:[/yellow] {plugin_name}\n"
            f"  Junction: {link_path}"
        )
        # Ensure cache entry exists
        if not cache_version_path.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            try:
                create_link(cache_version_path, plugin_path)
                console.print(f"  Cache entry created: {cache_version_path}")
            except JunctionError as e:
                console.print(f"  [yellow]Warning: cache junction failed:[/yellow] {e}")
        # Update all registry entries to ensure consistency
        install_path = str(cache_version_path)
        add_installed_plugin(plugin_name, install_path, version=plugin_version)
        add_marketplace_plugin(plugin_name, plugin_description, plugin_version, plugin_author)
        enable_plugin(plugin_name)
        console.print("  Registry entries refreshed.")
        return

    # Create marketplace junction
    try:
        create_link(link_path, plugin_path)
    except JunctionError as e:
        console.print(f"[red]Failed to create junction:[/red] {e}")
        raise typer.Exit(code=1)

    # Create cache junction — Claude Code loads plugins from here
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        if cache_version_path.exists():
            remove_link(cache_version_path)
        create_link(cache_version_path, plugin_path)
    except JunctionError as e:
        console.print(f"[yellow]Warning: cache junction failed:[/yellow] {e}")
        # Non-fatal: marketplace junction still works as fallback

    # Update registry — rollback junctions if this fails
    try:
        install_path = str(cache_version_path)
        add_installed_plugin(plugin_name, install_path, version=plugin_version)
        add_marketplace_plugin(plugin_name, plugin_description, plugin_version, plugin_author)
        enable_plugin(plugin_name)
    except Exception as e:
        # Rollback: remove the junctions we just created
        try:
            remove_link(link_path)
        except JunctionError:
            pass
        try:
            remove_link(cache_version_path)
        except JunctionError:
            pass
        console.print(f"[red]Failed to update registry:[/red] {e}")
        console.print("  Junctions rolled back.")
        raise typer.Exit(code=1)

    console.print(f"[green]Plugin registered:[/green] {plugin_name}")
    console.print(f"  Source:   {plugin_path}")
    console.print(f"  Junction: {link_path}")
    console.print(f"  Cache:    {cache_version_path}")
    console.print(f"  Version:  {plugin_version}")
