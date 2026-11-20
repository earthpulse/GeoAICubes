"""Zarr inventory API models (Step 1 D2). Wired to routes in I4."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ZarrStoreStatus = Literal["ok", "error"]


class InventoryVariable(BaseModel):
    name: str
    dtype: str
    shape: list[int]


class InventoryExtent(BaseModel):
    bbox: tuple[float, float, float, float] = Field(
        ...,
        description="[minx, miny, maxx, maxy] in extent.crs",
    )
    crs: str


class InventoryTime(BaseModel):
    dim: str
    values: list[str] | None = None
    start: str | None = None
    end: str | None = None
    count: int | None = None


RenderMode = Literal["rgb", "single", "categorical"]


class ExtraDimInfo(BaseModel):
    name: str
    kind: Literal["nominal", "ordinal", "datetime"]
    labels: list[str]


class RenderDefaults(BaseModel):
    mode: RenderMode
    sel: dict[str, list[str]] = Field(default_factory=dict)
    bidx: list[int] | None = None
    rescale: list[tuple[float, float]]
    colormap_name: str | None = None
    colormap: dict[int, list[int]] | None = None


class LegendEntry(BaseModel):
    value: int
    label: str
    color: str


class RenderCapability(BaseModel):
    modes: list[RenderMode]
    variable: str
    extra_dims: list[ExtraDimInfo]
    defaults: RenderDefaults
    legend: list[LegendEntry] = Field(default_factory=list)
    primary: bool = False


class ZarrStoreInventory(BaseModel):
    id: str
    uri: str
    path: str
    status: ZarrStoreStatus
    error: str | None
    dims: list[str]
    variables: list[InventoryVariable]
    crs: str | None
    extent: InventoryExtent | None
    time: InventoryTime | None = None
    nodata: dict[str, float | int | None]
    chunks: dict[str, dict[str, int]]
    tile_url_template: dict[str, str]
    render_capabilities: dict[str, RenderCapability] = Field(default_factory=dict)


class ZarrInventoryList(BaseModel):
    stores: list[ZarrStoreInventory]
    count: int