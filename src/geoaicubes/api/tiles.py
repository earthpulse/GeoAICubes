"""TiTiler Xarray mount for GeoAICubes API (Step 1 I5)."""

from __future__ import annotations

from fastapi import FastAPI
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.xarray.extensions import DatasetMetadataExtension, ValidateExtension
from titiler.xarray.factory import TilerFactory

from geoaicubes.io.s3 import apply_s3_env

TILE_MOUNT_PREFIX = "/tiles/zarr"


def mount_zarr_tiler(app: FastAPI) -> None:
    """Register multidimensional tile routes under ``/tiles/zarr``."""
    apply_s3_env()
    tiler = TilerFactory(
        extensions=[
            DatasetMetadataExtension(),
            ValidateExtension(),
        ],
        router_prefix=TILE_MOUNT_PREFIX,
    )
    app.include_router(
        tiler.router,
        prefix=TILE_MOUNT_PREFIX,
        tags=["tiles"],
    )
    add_exception_handlers(app, DEFAULT_STATUS_CODES)
