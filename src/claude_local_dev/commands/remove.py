"""claude-local-dev remove — unregister a plugin."""

from __future__ import annotations

import typer
from rich.console import Console

from claude_local_dev.cli import app
from claude_local_dev.config import get_local_dev_plugins_dir
from claude_local_dev.errors import JunctionError
from claude_local_dev.junction import is_link, remove_link
from claude_local_dev.registry import (
    disable_plugin,
    get_installed_plugin,
    remove_installed_plugin,
)

console = Console()


@app.command()
def remove(
    plugin_name: str = typer.Argument(..., help="Name of the plugin to remove."),
) -> None:
    """Unregister a plugin: remove junction and clean up all registry entries."""
    plugins_dir = get_local_dev_plugins_dir()
    link_path = plugins_dir / plugin_name

    # Check if anything to remove
    has_junction = is_link(link_path)
    has_install = get_installed_plugin(plugin_name) is not None

    if not has_junction and not has_install:
        console.print(f"[yellow]Plugin not found:[/yellow] {plugin_name}")
        raise typer.Exit(code=1)

    # Clean registry first (safer: if junction removal fails, at least
    # the plugin is deregistered and won't load next session)
    remove_installed_plugin(plugin_name)
    disable_plugin(plugin_name)

    # Then remove junction
    if has_junction:
        try:
            remove_link(link_path)
            console.print(f"  Junction removed: {link_path}")
        except JunctionError as e:
            console.print(f"[red]Failed to remove junction:[/red] {e}")
    elif link_path.exists():
        console.print(
            f"  [yellow]Warning:[/yellow] {link_path} exists but is not a junction"
        )

    console.print(f"[green]Plugin removed:[/green] {plugin_name}")
