"""Liveness and readiness probes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from geoaicubes import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    """Process is up (no dependency checks)."""
    return {
        "status": "ok",
        "service": "geoaicubes-api",
        "version": __version__,
    }


@router.get("/ready")
def ready(request: Request) -> dict[str, Any]:
    """Configuration loaded at startup; safe to route demo traffic."""
    demo_config = getattr(request.app.state, "demo_config", None)
    if demo_config is None:
        return {
            "status": "not_ready",
            "demo_config_loaded": False,
        }
    return {
        "status": "ready",
        "demo_config_loaded": True,
        "demo_name": demo_config.name,
    }