"""Discover and introspect GeoDataCube Zarr stores (Step 1 I2)."""

from __future__ import annotations

import contextlib
import logging
import re
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import xarray as xr

from geoaicubes.api.schemas.inventory import (
    InventoryExtent,
    InventoryTime,
    InventoryVariable,
    ZarrInventoryList,
    ZarrStoreInventory,
)
from geoaicubes.config import StorageSettings, get_storage_settings
from geoaicubes.io.render import (
    encode_query_pairs,
    infer_store_render_capabilities,
    titiler_query_from_defaults,
)
from geoaicubes.io.s3 import get_s3_filesystem, zarr_mapper_for_uri

logger = logging.getLogger(__name__)

EPSG_AUTHORITY = re.compile(r'AUTHORITY\["EPSG","(\d+)"\]', re.IGNORECASE)
# WKT auxiliary codes (units, ellipsoid, etc.) — not CRS identifiers
_AUXILIARY_EPSG = frozenset({9001, 9122, 8901, 7019, 6258, 1024, 6326})
_WKT_CRS_ALIASES = {
    "ETRS89 / UTM zone 31N": "EPSG:25831",
    "WGS 84 / UTM zone 31N": "EPSG:32631",
}
SPATIAL_DIMS = frozenset({"x", "y", "X", "Y", "lon", "lat", "longitude", "latitude"})
TIME_VALUES_MAX = 48
TILE_MATRIX_SET = "WebMercatorQuad"
TILE_URL_PREFIX = "/tiles/zarr"


def list_zarr_inventory(
    settings: StorageSettings | None = None,
) -> ZarrInventoryList:
    cfg = settings or get_storage_settings()
    store_ids = discover_store_ids(cfg)
    stores = [introspect_store(store_id, cfg) for store_id in store_ids]
    return ZarrInventoryList(stores=stores, count=len(stores))


def discover_store_ids(settings: StorageSettings) -> list[str]:
    if settings.discovery_mode == "s3":
        return _discover_s3(settings)
    return _discover_filesystem(settings)


def _discover_filesystem(settings: StorageSettings) -> list[str]:
    root = settings.local_zarr_root()
    if not root.is_dir():
        logger.warning("Zarr root missing: %s", root)
        return []
    ids = sorted(
        p.name for p in root.iterdir() if p.is_dir() and p.name.endswith(".zarr")
    )
    return ids


def _discover_s3(settings: StorageSettings) -> list[str]:
    fs = get_s3_filesystem(settings)
    base = f"{settings.bucket}/{settings.prefix}/"
    try:
        names = fs.ls(base, detail=False)
    except FileNotFoundError:
        logger.warning("S3 prefix missing: %s", base)
        return []
    ids: list[str] = []
    for name in names:
        leaf = name.rstrip("/").split("/")[-1]
        if leaf.endswith(".zarr"):
            ids.append(leaf)
    return sorted(ids)


def introspect_store(store_id: str, settings: StorageSettings) -> ZarrStoreInventory:
    uri = settings.store_s3_uri(store_id)
    path = (
        settings.store_s3_uri(store_id)
        if settings.discovery_mode == "s3"
        else settings.store_host_path(store_id)
    )
    try:
        ds = _open_dataset(settings, store_id)
        try:
            return _build_ok_inventory(store_id, uri, path, ds, settings)
        finally:
            with contextlib.suppress(Exception):
                ds.close()
    except Exception as exc:
        logger.exception("Inventory failed for %s", store_id)
        return _error_inventory(store_id, uri, path, str(exc))


def _open_dataset(settings: StorageSettings, store_id: str) -> xr.Dataset:
    target = settings.store_open_target(store_id)
    if settings.discovery_mode == "s3":
        assert isinstance(target, str)
        mapper = zarr_mapper_for_uri(target, settings)
        return xr.open_zarr(mapper, consolidated=True)
    path = Path(target)
    return xr.open_zarr(path, consolidated=True)


def open_dataset_for_tests(settings: StorageSettings, store_id: str) -> xr.Dataset:
    """Open a demo Zarr store on disk or S3 (tests and notebooks)."""
    return _open_dataset(settings, store_id)


def _build_ok_inventory(
    store_id: str,
    uri: str,
    path: str,
    ds: xr.Dataset,
    settings: StorageSettings,
) -> ZarrStoreInventory:
    dims = _dataset_dims(ds)
    variables = _inventory_variables(ds)
    crs = extract_crs(ds)
    extent = compute_extent(ds, crs)
    time_info = extract_time(ds)
    nodata = {v.name: _var_nodata(ds, v.name) for v in variables}
    chunks = {v.name: _var_chunks(ds, v.name) for v in variables}
    render_capabilities = infer_store_render_capabilities(ds, time_info)
    tile_url_template = _tile_templates(
        store_id, ds, uri, path, time_info, settings, crs, render_capabilities
    )
    return ZarrStoreInventory(
        id=store_id,
        uri=uri,
        path=path,
        status="ok",
        error=None,
        dims=dims,
        variables=variables,
        crs=crs,
        extent=extent,
        time=time_info,
        nodata=nodata,
        chunks=chunks,
        tile_url_template=tile_url_template,
        render_capabilities=render_capabilities,
    )


def _error_inventory(
    store_id: str,
    uri: str,
    path: str,
    message: str,
) -> ZarrStoreInventory:
    return ZarrStoreInventory(
        id=store_id,
        uri=uri,
        path=path,
        status="error",
        error=message,
        dims=[],
        variables=[],
        crs=None,
        extent=None,
        time=None,
        nodata={},
        chunks={},
        tile_url_template={},
        render_capabilities={},
    )


def _dataset_dims(ds: xr.Dataset) -> list[str]:
    if ds.data_vars:
        primary = max(ds.data_vars, key=lambda n: int(np.prod(ds[n].shape)))
        return list(ds[primary].dims)
    return list(ds.dims)


def _inventory_variables(ds: xr.Dataset) -> list[InventoryVariable]:
    out: list[InventoryVariable] = []
    for name in sorted(ds.data_vars):
        da = ds[name]
        out.append(
            InventoryVariable(
                name=name,
                dtype=str(da.dtype),
                shape=[int(s) for s in da.shape],
            )
        )
    return out


def extract_crs(ds: xr.Dataset) -> str | None:
    if "spatial_ref" in ds:
        attrs = ds["spatial_ref"].attrs
        for key in ("epsg_code", "EPSG", "crs", "grid_crs"):
            val = attrs.get(key)
            if val is not None and str(val).strip():
                code = str(val).removeprefix("EPSG:")
                if code.isdigit():
                    return f"EPSG:{code}"
        for key in ("crs_wkt", "spatial_ref", "crs"):
            wkt = attrs.get(key)
            if isinstance(wkt, str):
                parsed = _crs_from_wkt(wkt)
                if parsed:
                    return parsed
    return None


def _crs_from_wkt(wkt: str) -> str | None:
    for label, epsg in _WKT_CRS_ALIASES.items():
        if label in wkt:
            return epsg
    matches = EPSG_AUTHORITY.findall(wkt)
    codes = [int(m) for m in matches if int(m) not in _AUXILIARY_EPSG]
    if codes:
        return f"EPSG:{codes[-1]}"
    return None


def compute_extent(ds: xr.Dataset, crs: str | None) -> InventoryExtent | None:
    crs = crs or extract_crs(ds)
    bbox = _extent_from_xy(ds)
    if bbox is None:
        bbox = _extent_from_geotransform(ds)
    if bbox is None or crs is None:
        return None
    return InventoryExtent(bbox=bbox, crs=crs)


def _extent_from_xy(ds: xr.Dataset) -> tuple[float, float, float, float] | None:
    x_name = next((c for c in ("x", "X", "lon", "longitude") if c in ds.coords), None)
    y_name = next((c for c in ("y", "Y", "lat", "latitude") if c in ds.coords), None)
    if not x_name or not y_name:
        return None
    x = ds.coords[x_name]
    y = ds.coords[y_name]
    if x.size == 0 or y.size == 0:
        return None
    xmin, xmax = float(x.min()), float(x.max())
    ymin, ymax = float(y.min()), float(y.max())
    if xmin > xmax:
        xmin, xmax = xmax, xmin
    if ymin > ymax:
        ymin, ymax = ymax, ymin
    return (xmin, ymin, xmax, ymax)


def _extent_from_geotransform(
    ds: xr.Dataset,
) -> tuple[float, float, float, float] | None:
    if "spatial_ref" not in ds:
        return None
    gt = ds["spatial_ref"].attrs.get("GeoTransform")
    if not gt or not isinstance(gt, str):
        return None
    parts = gt.split()
    if len(parts) < 6:
        return None
    origin_x, pixel_x, _, origin_y, _, pixel_y = (float(p) for p in parts[:6])
    if "x" not in ds.coords or "y" not in ds.coords:
        return None
    width = int(ds.sizes["x"])
    height = int(ds.sizes["y"])
    xmax = origin_x + pixel_x * width
    ymin = origin_y + pixel_y * height
    xmin = min(origin_x, xmax)
    xmax = max(origin_x, xmax)
    y_lo = min(origin_y, ymin)
    y_hi = max(origin_y, ymin)
    return (xmin, y_lo, xmax, y_hi)


def extract_time(ds: xr.Dataset) -> InventoryTime | None:
    time_name = next(
        (d for d in ("time", "t", "Time") if d in ds.dims or d in ds.coords),
        None,
    )
    if not time_name or time_name not in ds.coords:
        return None
    coord = ds.coords[time_name]
    count = int(ds.sizes.get(time_name, coord.size))
    if count == 0:
        return InventoryTime(dim=time_name, count=0, values=None, start=None, end=None)
    series = pd.to_datetime(coord.values, errors="coerce")
    valid = series[~pd.isna(series)]
    start = end = None
    values: list[str] | None = None
    if len(valid):
        start = pd.Timestamp(valid[0]).isoformat().replace("+00:00", "Z")
        end = pd.Timestamp(valid[-1]).isoformat().replace("+00:00", "Z")
    if count <= TIME_VALUES_MAX:
        values = [_iso_timestamp(v) for v in series]
    return InventoryTime(
        dim=time_name,
        values=values,
        start=start,
        end=end,
        count=count,
    )


def _iso_timestamp(value: object) -> str:
    if pd.isna(value):
        return "NaT"
    return pd.Timestamp(value).isoformat().replace("+00:00", "Z")


def _var_nodata(ds: xr.Dataset, name: str) -> float | int | None:
    da = ds[name]
    for key in ("_FillValue", "missing_value", "nodata"):
        if key in da.attrs:
            val = da.attrs[key]
            if val is None:
                return None
            if isinstance(val, (int, float, np.integer, np.floating)):
                return int(val) if isinstance(val, (int, np.integer)) else float(val)
    fill = da.encoding.get("_FillValue")
    if fill is not None and isinstance(fill, (int, float, np.integer, np.floating)):
        return int(fill) if isinstance(fill, (int, np.integer)) else float(fill)
    return None


def _var_chunks(ds: xr.Dataset, name: str) -> dict[str, int]:
    da = ds[name]
    raw = da.encoding.get("chunks")
    if not raw:
        return {}
    if isinstance(raw, tuple | list):
        return {dim: int(size) for dim, size in zip(da.dims, raw, strict=False)}
    if isinstance(raw, dict):
        return {str(k): int(v) for k, v in raw.items()}
    return {}


def _is_renderable(dims: tuple[str, ...]) -> bool:
    return len(set(dims) & SPATIAL_DIMS) >= 2


def _tile_dataset_url(
    store_id: str,
    uri: str,
    path: str,
    settings: StorageSettings,
) -> str:
    """Location passed as TiTiler ``?url=`` (filesystem path or s3 URI)."""
    if settings.discovery_mode == "filesystem":
        target = settings.store_open_target(store_id)
        assert not isinstance(target, str)
        return target.resolve().as_posix()
    return uri


def _tile_templates(
    store_id: str,
    ds: xr.Dataset,
    uri: str,
    path: str,
    time_info: InventoryTime | None,
    settings: StorageSettings,
    crs: str | None,
    render_capabilities: dict,
) -> dict[str, str]:
    dataset_url = quote(_tile_dataset_url(store_id, uri, path, settings), safe="")
    crs_sel = f"&coord_crs={quote(crs, safe='')}" if crs else ""

    templates: dict[str, str] = {}
    for name in sorted(ds.data_vars):
        da = ds[name]
        if not _is_renderable(da.dims):
            continue
        variable = quote(name, safe="")
        cap = render_capabilities.get(name)
        if cap is None:
            continue
        time_label = time_info.start if time_info else None
        vis_pairs = titiler_query_from_defaults(cap, time_label=time_label)
        vis_q = encode_query_pairs(vis_pairs)
        query = f"url={dataset_url}&variable={variable}&{vis_q}{crs_sel}"
        templates[name] = (
            f"{TILE_URL_PREFIX}/tiles/{TILE_MATRIX_SET}/{{z}}/{{x}}/{{y}}.png?{query}"
        )
    return templates


def get_store_inventory(
    store_id: str,
    settings: StorageSettings | None = None,
) -> ZarrStoreInventory | None:
    """Return one store if it exists in the current discovery set."""
    cfg = settings or get_storage_settings()
    if store_id not in discover_store_ids(cfg):
        return None
    return introspect_store(store_id, cfg)
