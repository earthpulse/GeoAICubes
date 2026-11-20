"""Infer TiTiler visualization capabilities from Zarr metadata.

No store-name hardcoding — driven by xarray structure and coords.
"""

from __future__ import annotations

import json
from typing import Literal
from urllib.parse import quote

import numpy as np
import pandas as pd
import xarray as xr

from geoaicubes.api.schemas.inventory import (
    ExtraDimInfo,
    InventoryTime,
    LegendEntry,
    RenderCapability,
    RenderDefaults,
    RenderMode,
)

_SPATIAL = frozenset({"x", "y", "X", "Y", "lon", "lat", "longitude", "latitude"})
_BAND_DIMS = frozenset({"band", "bands", "wavelength"})
_NOMINAL_RGB = ("RED", "GRN", "BLU")
# GeoDataCube S2-style stacks: band coord 0..9 → default visual RGB uses B4,B3,B2.
_S2_RGB_BAND_VALUES = ("3", "2", "1")

RenderModeList = list[RenderMode]


def _primary_variable(ds: xr.Dataset) -> str | None:
    renderable = [
        name for name in ds.data_vars if len(set(ds[name].dims) & _SPATIAL) >= 2
    ]
    if not renderable:
        return None
    return max(renderable, key=lambda n: int(np.prod(ds[n].shape)))


def _coord_labels(da: xr.DataArray, dim: str) -> list[str]:
    if dim not in da.coords:
        return [str(i) for i in range(int(da.sizes.get(dim, 0)))]
    coord = da.coords[dim]
    out: list[str] = []
    for v in coord.values:
        if isinstance(v, (bytes, np.bytes_)):
            out.append(v.decode() if isinstance(v, bytes) else str(v))
        elif isinstance(v, np.datetime64) or hasattr(v, "isoformat"):
            out.append(pd.Timestamp(v).isoformat().replace("+00:00", "Z"))
        else:
            out.append(str(int(v)) if isinstance(v, (np.integer, int)) else str(v))
    return out


def _extra_dim_infos(da: xr.DataArray) -> list[ExtraDimInfo]:
    infos: list[ExtraDimInfo] = []
    for dim in da.dims:
        if dim in _SPATIAL or dim in {"spatial_ref", "crs_wkt", "grid_mapping"}:
            continue
        labels = _coord_labels(da, dim)
        if dim in ("time", "t", "Time"):
            kind: Literal["nominal", "ordinal", "datetime"] = "datetime"
        elif dim in _BAND_DIMS and labels and not labels[0].isdigit():
            kind = "nominal"
        else:
            kind = "ordinal"
        infos.append(ExtraDimInfo(name=dim, kind=kind, labels=labels))
    return infos


def _default_rescale_per_band(dtype: str, bands: int) -> list[tuple[float, float]]:
    normalized = dtype.lower()
    if normalized in {"uint8", "int8"} or (
        normalized.startswith("uint") and "16" not in normalized
    ):
        pair = (0.0, 255.0)
    elif "16" in normalized:
        pair = (0.0, 65535.0)
    else:
        pair = (0.0, 3000.0)
    return [pair] * bands


def _dtype_is_integer(dtype: str) -> bool:
    normalized = dtype.lower()
    return (
        normalized.startswith("u") or normalized.startswith("i") or "int" in normalized
    )


def _rgb_sel_from_labels(labels: list[str]) -> list[str]:
    upper = {lab.upper(): lab for lab in labels}
    picks: list[str] = []
    for name in _NOMINAL_RGB:
        if name in upper:
            picks.append(upper[name])
    if len(picks) == 3:
        return picks
    # fall back to first three labels
    if len(labels) >= 3:
        return [labels[0], labels[1], labels[2]]
    return labels[:1]


def _s2_rgb_sel(band_info: ExtraDimInfo | None) -> list[str]:
    if band_info is None:
        return list(_S2_RGB_BAND_VALUES)
    labels = set(band_info.labels)
    picked = [v for v in _S2_RGB_BAND_VALUES if v in labels]
    if len(picked) == 3:
        return picked
    if len(band_info.labels) >= 3:
        return band_info.labels[:3]
    return band_info.labels[:1]


def _categorical_colormap(labels: list[str] | None = None) -> dict[int, list[int]]:
    """Simple distinct colors for integer class rasters (legend + TiTiler colormap)."""
    entries: dict[int, list[int]] = {0: [0, 0, 0, 0]}
    palette = [
        [215, 48, 39, 255],
        [244, 109, 67, 255],
        [253, 174, 97, 255],
        [254, 224, 139, 255],
        [255, 255, 191, 255],
        [199, 233, 180, 255],
        [145, 207, 96, 255],
        [91, 163, 63, 255],
        [39, 100, 25, 255],
        [49, 54, 149, 255],
        [69, 117, 180, 255],
        [116, 173, 209, 255],
        [171, 217, 233, 255],
        [224, 243, 248, 255],
        [165, 0, 38, 255],
        [215, 48, 39, 255],
    ]
    if labels:
        for i, _lab in enumerate(labels):
            cls = i + 1
            entries[cls] = palette[i % len(palette)]
    else:
        for cls in range(1, 25):
            entries[cls] = palette[(cls - 1) % len(palette)]
    return entries


def _legend_from_colormap(cmap: dict[int, list[int]]) -> list[LegendEntry]:
    items: list[LegendEntry] = []
    for value in sorted(k for k in cmap if k > 0):
        rgba = cmap[value]
        alpha = (rgba[3] if len(rgba) > 3 else 255) / 255
        items.append(
            LegendEntry(
                value=value,
                label=str(value),
                color=f"rgba({rgba[0]},{rgba[1]},{rgba[2]},{alpha:.2f})",
            )
        )
    return items[:24]


def infer_render_capability(
    ds: xr.Dataset,
    variable: str,
    time_info: InventoryTime | None,
) -> RenderCapability | None:
    if variable not in ds.data_vars:
        return None
    da = ds[variable]
    if len(set(da.dims) & _SPATIAL) < 2:
        return None

    extra_dims = _extra_dim_infos(da)
    band_dim = next((d for d in extra_dims if d.name in _BAND_DIMS), None)
    time_dim = next((d for d in extra_dims if d.kind == "datetime"), None)
    modes: RenderModeList = ["single"]

    sel: dict[str, list[str]] = {}
    bidx: list[int] | None = None
    rescale: list[tuple[float, float]]
    colormap: dict[int, list[int]] | None = None
    colormap_name: str | None = None
    legend: list[LegendEntry] = []
    mode: RenderMode = "single"

    if band_dim is not None:
        modes = ["rgb", "single"]
        rgb_labels = _rgb_sel_from_labels(band_dim.labels)
        label_upper = {lab.upper() for lab in band_dim.labels}
        nominal_upper = {n.upper() for n in _NOMINAL_RGB}
        if label_upper >= nominal_upper:
            sel[band_dim.name] = _rgb_sel_from_labels(band_dim.labels)
        elif (
            band_dim.name == "band"
            and band_dim.kind == "ordinal"
            and len(band_dim.labels) >= 10
        ):
            sel[band_dim.name] = _s2_rgb_sel(band_dim)
        else:
            sel[band_dim.name] = rgb_labels
        mode = "rgb"
        bidx = [1, 2, 3] if len(sel.get(band_dim.name, [])) >= 3 else [1]
        rescale = _default_rescale_per_band(str(da.dtype), len(bidx))
    elif da.ndim == 2 and _dtype_is_integer(str(da.dtype)):
        modes = ["categorical", "single"]
        mode = "categorical"
        colormap = _categorical_colormap()
        legend = _legend_from_colormap(colormap)
        rescale = [(0.0, 255.0)]
    else:
        rescale = _default_rescale_per_band(str(da.dtype), 1)

    if time_dim is not None and time_info and time_info.start:
        sel[time_dim.name] = [time_info.start]

    return RenderCapability(
        modes=modes,
        variable=variable,
        extra_dims=extra_dims,
        defaults=RenderDefaults(
            mode=mode,
            sel=sel,
            bidx=bidx,
            rescale=rescale,
            colormap_name=colormap_name,
            colormap=colormap,
        ),
        legend=legend,
    )


def infer_store_render_capabilities(
    ds: xr.Dataset,
    time_info: InventoryTime | None,
) -> dict[str, RenderCapability]:
    out: dict[str, RenderCapability] = {}
    primary = _primary_variable(ds)
    for name in sorted(ds.data_vars):
        da = ds[name]
        if len(set(da.dims) & _SPATIAL) < 2:
            continue
        cap = infer_render_capability(ds, name, time_info)
        if cap is None:
            continue
        if name == primary:
            cap = cap.model_copy(update={"primary": True})
        out[name] = cap
    return out


def titiler_query_from_defaults(
    cap: RenderCapability,
    *,
    time_label: str | None = None,
    mode: RenderMode | None = None,
    band_selection: list[str] | None = None,
    band_dim: str | None = None,
) -> list[tuple[str, str]]:
    """Build repeated query key/value pairs for TiTiler tile requests."""
    defaults = cap.defaults
    use_mode = mode or defaults.mode
    pairs: list[tuple[str, str]] = []

    sel = dict(defaults.sel)
    if time_label:
        time_dim = next((d.name for d in cap.extra_dims if d.kind == "datetime"), None)
        if time_dim:
            sel[time_dim] = [time_label]

    band_d = band_dim or next(
        (d.name for d in cap.extra_dims if d.name in _BAND_DIMS),
        None,
    )
    if band_d and band_selection:
        sel[band_d] = band_selection

    for dim, values in sel.items():
        for value in values:
            pairs.append(("sel", f"{dim}={value}"))

    if use_mode == "rgb" and band_d:
        picks = sel.get(band_d, [])
        count = len(picks) if picks else 3
        bidx_list = defaults.bidx or list(range(1, count + 1))
        if len(bidx_list) < count:
            bidx_list = list(range(1, count + 1))
        for idx in bidx_list[:count]:
            pairs.append(("bidx", str(idx)))
        rescale = defaults.rescale
        if len(rescale) < count:
            rescale = _default_rescale_per_band("uint8", count)
        for lo, hi in rescale[:count]:
            pairs.append(("rescale", f"{lo},{hi}"))
    elif use_mode == "categorical":
        if defaults.colormap:
            cmap_json = json.dumps(defaults.colormap, separators=(",", ":"))
            pairs.append(("colormap", cmap_json))
        elif defaults.colormap_name:
            pairs.append(("colormap_name", defaults.colormap_name))
        else:
            lo, hi = defaults.rescale[0]
            pairs.append(("rescale", f"{lo},{hi}"))
    else:
        lo, hi = defaults.rescale[0]
        pairs.append(("rescale", f"{lo},{hi}"))

    return pairs


def encode_query_pairs(pairs: list[tuple[str, str]]) -> str:
    return "&".join(f"{quote(k, safe='')}={quote(v, safe=',=:')}" for k, v in pairs)
