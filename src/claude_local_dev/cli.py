"""Typer CLI application — command routing."""

from __future__ import annotations

import typer

from claude_local_dev import __version__

app = typer.Typer(
    name="claude-local-dev",
    help="Manage a local-dev marketplace for Claude Code plugins.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"claude-local-dev {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit.",
        callback=version_callback, is_eager=True,
    ),
) -> None:
    pass


# Import commands to register them
from claude_local_dev.commands import init as _init_cmd  # noqa: E402, F401
from claude_local_dev.commands import add as _add_cmd  # noqa: E402, F401
from claude_local_dev.commands import remove as _remove_cmd  # noqa: E402, F401
from claude_local_dev.commands import list as _list_cmd  # noqa: E402, F401
from claude_local_dev.commands import verify as _verify_cmd  # noqa: E402, F401


def main() -> None:
    app()
