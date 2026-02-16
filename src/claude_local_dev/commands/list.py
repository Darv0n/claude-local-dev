"""claude-local-dev list — show registered plugins with status."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from claude_local_dev.cli import app
from claude_local_dev.config import get_local_dev_cache_dir, get_local_dev_plugins_dir
from claude_local_dev.junction import is_link, is_link_healthy, link_target
from claude_local_dev.registry import (
    is_marketplace_registered,
    is_plugin_enabled,
    list_installed_local_dev_plugins,
)

console = Console()


@app.command(name="list")
def list_plugins() -> None:
    """Show registered local-dev plugins with status information."""
    if not is_marketplace_registered():
        console.print(
            "[yellow]Marketplace not initialized.[/yellow] Run `claude-local-dev init` first."
        )
        raise typer.Exit(code=1)

    installed = list_installed_local_dev_plugins()
    plugins_dir = get_local_dev_plugins_dir()
    cache_dir = get_local_dev_cache_dir()

    if not installed:
        console.print("[dim]No local-dev plugins registered.[/dim]")
        return

    table = Table(title="Local-Dev Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Enabled")
    table.add_column("Junction")
    table.add_column("Cache")
    table.add_column("Target")

    for name, records in sorted(installed.items()):
        version = records[0].get("version", "?") if records else "?"
        enabled = is_plugin_enabled(name)
        link_path = plugins_dir / name
        has_link = is_link(link_path)
        healthy = is_link_healthy(link_path) if has_link else False

        enabled_str = "[green]yes[/green]" if enabled else "[red]no[/red]"

        if has_link and healthy:
            junction_str = "[green]ok[/green]"
            target = link_target(link_path)
            target_str = str(target) if target else "?"
        elif has_link and not healthy:
            junction_str = "[red]broken[/red]"
            target = link_target(link_path)
            target_str = f"[red]{target}[/red]" if target else "[red]?[/red]"
        else:
            junction_str = "[red]missing[/red]"
            target_str = "[dim]-[/dim]"

        # Check cache status
        cache_version_path = cache_dir / name / version
        if cache_version_path.exists():
            cache_str = "[green]ok[/green]"
        else:
            cache_str = "[red]missing[/red]"

        table.add_row(name, version, enabled_str, junction_str, cache_str, target_str)

    console.print(table)
