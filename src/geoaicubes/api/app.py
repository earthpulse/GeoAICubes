"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from geoaicubes import __version__
from geoaicubes.api.routes import health, inventory
from geoaicubes.api.tiles import mount_zarr_tiler
from geoaicubes.io.s3 import apply_s3_env
from geoaicubes.logging_config import configure_logging

logger = logging.getLogger(__name__)

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


def cors_allow_origins() -> list[str]:
    raw = os.environ.get("GEOAICUBES_CORS_ORIGINS", "").strip()
    if not raw:
        return list(_DEFAULT_CORS_ORIGINS)
    return [part.strip() for part in raw.split(",") if part.strip()]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    configure_logging()
    apply_s3_env()
    logger.info("GeoAICubes API ready")
    yield


def create_app(**kwargs: Any) -> FastAPI:
    app = FastAPI(
        title="GeoAICubes API",
        description="EarthPulse demo API.",
        version=__version__,
        lifespan=kwargs.pop("lifespan", _lifespan),
        **kwargs,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(inventory.router, prefix="/api/v1")
    mount_zarr_tiler(app)
    return app
