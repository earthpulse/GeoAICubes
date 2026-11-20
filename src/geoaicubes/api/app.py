"""FastAPI application factory."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from geoaicubes import __version__
from geoaicubes.config import DemoConfig, load_demo_config
from geoaicubes.logging_config import configure_logging
from geoaicubes.api.routes import health, v1

logger = logging.getLogger(__name__)

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


def cors_allow_origins() -> list[str]:
    """Dev UI origins from ``GEOAICUBES_CORS_ORIGINS`` (comma-separated) or localhost defaults."""
    raw = os.environ.get("GEOAICUBES_CORS_ORIGINS", "").strip()
    if not raw:
        return list(_DEFAULT_CORS_ORIGINS)
    return [part.strip() for part in raw.split(",") if part.strip()]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    configure_logging()
    demo_config = load_demo_config()
    app.state.demo_config = demo_config
    logger.info("GeoAICubes API ready (demo=%s)", demo_config.name)
    yield


def create_app(*, demo_config: DemoConfig | None = None, **kwargs: Any) -> FastAPI:
    """
    Build the GeoAICubes API application.

    Parameters
    ----------
    demo_config:
        Optional pre-loaded config (tests). When omitted, ``load_demo_config`` runs at startup.
    """
    lifespan = kwargs.pop("lifespan", None)
    if lifespan is None and demo_config is None:
        lifespan = _lifespan
    elif demo_config is not None:
        @asynccontextmanager
        async def _inject_config(app: FastAPI):
            app.state.demo_config = demo_config
            yield

        lifespan = _inject_config

    app = FastAPI(
        title="GeoAICubes API",
        description="EarthPulse demo API — viewer and export entry points.",
        version=__version__,
        lifespan=lifespan,
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
    app.include_router(v1.router)

    return app