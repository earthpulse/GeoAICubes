"""Uvicorn entry: ``uv run uvicorn geoaicubes.api.main:app``."""

from __future__ import annotations

import os

from geoaicubes.api.app import create_app

app = create_app()


def main() -> None:
    import uvicorn

    reload = os.environ.get("GEOAICUBES_API_RELOAD", "").lower() in {"1", "true", "yes"}
    uvicorn.run(
        "geoaicubes.api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("GEOAICUBES_API_PORT", "8000")),
        reload=reload,
    )


if __name__ == "__main__":
    main()
