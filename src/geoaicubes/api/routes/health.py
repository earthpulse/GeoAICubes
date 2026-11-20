"""Liveness probe."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from geoaicubes import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "geoaicubes-api",
        "version": __version__,
    }