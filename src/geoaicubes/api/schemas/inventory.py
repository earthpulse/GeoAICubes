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


class ZarrInventoryList(BaseModel):
    stores: list[ZarrStoreInventory]
    count: int