"""GeoAICubes Typer CLI.

Top-level command tree (Wave 1 stubs):

- ``version`` — installed package version
- ``data`` — dataset list/sync placeholders (no download logic here)
- ``bench`` — performance benchmark placeholders (D1.3)
- ``train`` — offline training placeholders (D2.2)

Planned delegation: ``data`` sync/list will call ``scripts/fetch_datacloud.py``
(see ``Makefile`` targets such as ``sync-geodatacubes``) in a later step — do not
duplicate fetch logic in this module until that wiring lands.
"""

from __future__ import annotations

import typer

from geoaicubes import __version__
from geoaicubes.logging_config import configure_logging

app = typer.Typer(
    name="geoaicubes",
    help="EarthPulse GeoAICubes — ICGC datacloud demo stack.",
    no_args_is_help=True,
)

data_app = typer.Typer(
    help="Data access stubs. Sync will delegate to scripts/fetch_datacloud.py via Makefile.",
    no_args_is_help=True,
)
bench_app = typer.Typer(
    help="Benchmark stubs (D1.3 performance guide).",
    no_args_is_help=True,
)
train_app = typer.Typer(
    help="Training stubs (D2.2 offline classification).",
    no_args_is_help=True,
)

app.add_typer(data_app, name="data")
app.add_typer(bench_app, name="bench")
app.add_typer(train_app, name="train")


@app.callback()
def _cli_entry() -> None:
    """Initialize shared logging before subcommands run."""
    configure_logging()


@app.command("version")
def version_command() -> None:
    """Show the installed geoaicubes version."""
    typer.echo(__version__)


@data_app.callback()
def _data_group() -> None:
    """Placeholder for future data subcommands (list, sync, …)."""


@data_app.command("list")
def data_list() -> None:
    """List demo datasets (stub; use ``make list-geodatacubes`` until wired)."""
    typer.echo("data list: stub — not implemented (see Makefile sync/list targets)")


@data_app.command("sync")
def data_sync() -> None:
    """Sync demo datasets (stub; will delegate to scripts/fetch_datacloud.py)."""
    typer.echo("data sync: stub — not implemented (see Makefile sync-geodatacubes)")


@bench_app.callback()
def _bench_group() -> None:
    """Placeholder for future benchmark subcommands."""


@bench_app.command("run")
def bench_run() -> None:
    """Run D1.3 performance benchmarks (stub)."""
    typer.echo("bench run: stub — not implemented")


@train_app.callback()
def _train_group() -> None:
    """Placeholder for future training subcommands."""


@train_app.command("run")
def train_run() -> None:
    """Run offline classification training (stub)."""
    typer.echo("train run: stub — not implemented")


def main() -> None:
    """Console script entry (see ``[project.scripts]`` in pyproject.toml)."""
    app()


if __name__ == "__main__":
    main()