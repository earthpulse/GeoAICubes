"""GeoAICubes CLI — smoke check only until feature commands land."""

from __future__ import annotations

import typer

from geoaicubes import __version__
from geoaicubes.logging_config import configure_logging

app = typer.Typer(
    name="geoaicubes",
    help="EarthPulse GeoAICubes — ICGC datacloud demo stack.",
    no_args_is_help=True,
)


@app.callback()
def _cli_entry() -> None:
    configure_logging()


@app.command("ok")
def ok_command() -> None:
    """Smoke check: package imports and reports version."""
    typer.echo(f"geoaicubes {__version__}: ok")


def main() -> None:
    app()


if __name__ == "__main__":
    main()