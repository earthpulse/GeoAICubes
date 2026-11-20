"""I/O stubs — cube open and path resolution (D1.1 / D1.2; no geospatial logic yet)."""

from __future__ import annotations

from pathlib import Path

from geoaicubes.config import DemoConfig

__all__ = ["open_cube", "resolve_data_path"]


def open_cube(uri: str, *, config: DemoConfig | None = None) -> dict[str, str]:
    """
    Placeholder for Zarr / xarray open paths used by notebooks and the API.

    Returns stub metadata until D1.2 implements real reads.
    """
    _ = config
    return {
        "implementation": "stub",
        "operation": "open_cube",
        "uri": uri,
        "note": "No cube I/O in Step 0 scaffold.",
    }


def resolve_data_path(relative: str | Path, *, config: DemoConfig) -> Path:
    """Resolve a path under ``config.paths.data_root`` (absolute paths unchanged)."""
    path = Path(relative)
    if path.is_absolute():
        return path
    return (config.paths.data_root / path).resolve()