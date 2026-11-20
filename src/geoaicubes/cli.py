"""GeoAICubes CLI — smoke check only until feature commands land."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import typer

from geoaicubes import __version__
from geoaicubes.logging_config import configure_logging

DEFAULT_INVENTORY_EXPORT = Path("config/inventory-export.json")

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


def _inventory_list_payload() -> dict:
    from geoaicubes.io.inventory import list_zarr_inventory

    return list_zarr_inventory().model_dump(mode="json")


def _inventory_from_api(api_base: str) -> dict:
    url = f"{api_base.rstrip('/')}/api/v1/inventory/zarr"
    try:
        with urlopen(url, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as exc:
        typer.secho(f"GET {url} failed ({exc.code}): {exc.reason}", err=True)
        raise typer.Exit(code=1) from exc
    except URLError as exc:
        typer.secho(f"GET {url} failed: {exc.reason}", err=True)
        raise typer.Exit(code=1) from exc


@app.command("inventory-list")
def inventory_list_command() -> None:
    """List and introspect Zarr stores under the configured data root."""
    typer.echo(json.dumps(_inventory_list_payload(), indent=2))


@app.command("inventory-export")
def inventory_export_command(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Path for the JSON snapshot (repo-relative by default).",
        ),
    ] = DEFAULT_INVENTORY_EXPORT,
    api_base: Annotated[
        str | None,
        typer.Option(
            "--api-base",
            envvar="GEOAICUBES_API_BASE_URL",
            help="Fetch live inventory from a running API (else use in-process I/O).",
        ),
    ] = None,
) -> None:
    """Write ``GET /api/v1/inventory/zarr`` payload to disk for filing."""
    payload = _inventory_from_api(api_base) if api_base else _inventory_list_payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    store_count = payload.get("count", len(payload.get("stores", [])))
    typer.echo(f"Wrote {output} ({store_count} stores)")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
