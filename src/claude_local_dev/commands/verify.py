"""claude-local-dev verify — cross-reference all registry files for consistency."""

from __future__ import annotations

import typer
from rich.console import Console

from claude_local_dev.cli import app
from claude_local_dev.config import get_local_dev_plugins_dir, MARKETPLACE_NAME
from claude_local_dev.junction import is_link, is_link_healthy, link_target
from claude_local_dev.registry import (
    is_marketplace_registered,
    list_enabled_local_dev_plugins,
    list_installed_local_dev_plugins,
)

console = Console()


@app.command()
def verify() -> None:
    """Cross-reference all registry files and report mismatches."""
    issues: list[str] = []

    # Check marketplace registration
    if not is_marketplace_registered():
        issues.append("Marketplace 'local-dev' not registered in known_marketplaces.json")

    # Gather data from each source
    enabled_names = set(list_enabled_local_dev_plugins())
    installed_names = set(list_installed_local_dev_plugins().keys())
    plugins_dir = get_local_dev_plugins_dir()

    # Scan junction directory
    junction_names: set[str] = set()
    if plugins_dir.exists():
        for entry in plugins_dir.iterdir():
            if is_link(entry):
                junction_names.add(entry.name)

    all_names = enabled_names | installed_names | junction_names

    for name in sorted(all_names):
        link_path = plugins_dir / name

        # Check: enabled but not installed
        if name in enabled_names and name not in installed_names:
            issues.append(
                f"{name}: enabled in settings.json but missing from installed_plugins.json"
            )

        # Check: installed but not enabled
        if name in installed_names and name not in enabled_names:
            issues.append(
                f"{name}: in installed_plugins.json but not enabled in settings.json"
            )

        # Check: registry entry but no junction
        if (name in enabled_names or name in installed_names) and name not in junction_names:
            issues.append(
                f"{name}: registered but no junction in {plugins_dir}"
            )

        # Check: junction but no registry entry
        if name in junction_names and name not in installed_names:
            issues.append(
                f"{name}: junction exists but not in installed_plugins.json"
            )

        # Check: broken junction
        if name in junction_names:
            if not is_link_healthy(link_path):
                target = link_target(link_path)
                issues.append(
                    f"{name}: junction target missing or inaccessible ({target})"
                )

    # Report
    if issues:
        console.print(f"[red]Found {len(issues)} issue(s):[/red]")
        for issue in issues:
            console.print(f"  [yellow]![/yellow] {issue}")
        raise typer.Exit(code=1)
    else:
        n = len(all_names)
        console.print(
            f"[green]No issues found.[/green] {n} plugin(s) verified."
        )
