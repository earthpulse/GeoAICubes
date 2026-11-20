"""Versioned API stubs — structured placeholders until library-backed routes (Step 5)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1", tags=["v1"])


def _stub_meta(*, status: str = "stub") -> dict[str, str]:
    return {"implementation": status, "note": "No geospatial processing in Step 0 scaffold."}


@router.get("/meta")
def meta(request: Request) -> dict[str, Any]:
    """Public demo metadata derived from loaded config (no secrets)."""
    cfg = request.app.state.demo_config
    storage = cfg.storage
    return {
        **_stub_meta(),
        "name": cfg.name,
        "crs": cfg.crs,
        "bbox": cfg.bbox.model_dump(),
        "dates": cfg.dates.model_dump(),
        "class_count": len(cfg.classes),
        "storage": {
            "endpoint_url": storage.endpoint_url,
            "bucket": storage.bucket,
            "prefix": storage.prefix,
            "use_ssl": storage.use_ssl,
        },
    }


@router.get("/layers")
def layers(request: Request) -> dict[str, Any]:
    """Placeholder layer catalog for the viewer."""
    cfg = request.app.state.demo_config
    layers_list: list[dict[str, Any]] = [
        {
            "id": "cube",
            "type": "zarr",
            "title": "Demo datacube",
            "path": str(cfg.paths.data_root / cfg.paths.cube_zarr),
            "status": "stub",
        },
        {
            "id": "labels",
            "type": "raster",
            "title": "Reference labels",
            "path": str(cfg.paths.data_root / cfg.paths.label_raster),
            "status": "stub",
        },
    ]
    if cfg.paths.classification_output:
        layers_list.append(
            {
                "id": "classification",
                "type": "raster",
                "title": "Precomputed classification",
                "path": str(cfg.paths.data_root / cfg.paths.classification_output),
                "status": "stub",
            }
        )
    if cfg.paths.change_map_output:
        layers_list.append(
            {
                "id": "change_map",
                "type": "raster",
                "title": "Precomputed change map",
                "path": str(cfg.paths.data_root / cfg.paths.change_map_output),
                "status": "stub",
            }
        )
    return {**_stub_meta(), "layers": layers_list}


@router.get("/classes")
def classes(request: Request) -> dict[str, Any]:
    """Land-cover legend from demo config."""
    cfg = request.app.state.demo_config
    return {
        **_stub_meta(),
        "classes": [entry.model_dump() for entry in cfg.classes],
    }


@router.post("/query/timeseries")
def query_timeseries() -> dict[str, Any]:
    """Placeholder pixel/time series query (Step 5)."""
    return {
        **_stub_meta(),
        "query": {
            "lon": None,
            "lat": None,
            "time_range": None,
        },
        "values": [],
    }


@router.post("/export")
def export_asset() -> dict[str, Any]:
    """Placeholder export job (GeoTIFF/CSV — Step 5)."""
    return {
        **_stub_meta(),
        "job": {
            "id": "stub-job-00000000",
            "status": "pending",
            "formats": ["geotiff", "csv"],
            "download_url": None,
        },
    }