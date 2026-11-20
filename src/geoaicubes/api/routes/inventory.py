"""Zarr inventory HTTP routes (Step 1 I4)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from geoaicubes.api.schemas.inventory import ZarrInventoryList, ZarrStoreInventory
from geoaicubes.io.inventory import get_store_inventory, list_zarr_inventory

router = APIRouter(tags=["inventory"])


@router.get("/inventory/zarr", response_model=ZarrInventoryList)
def list_zarr_stores() -> ZarrInventoryList:
    """Enumerate every ``*.zarr`` under the configured storage root."""
    return list_zarr_inventory()


@router.get("/inventory/zarr/{store_id}", response_model=ZarrStoreInventory)
def get_zarr_store(store_id: str) -> ZarrStoreInventory:
    """Return inventory for one store id (basename including ``.zarr``)."""
    store = get_store_inventory(store_id)
    if store is None:
        raise HTTPException(status_code=404, detail=f"Unknown Zarr store: {store_id}")
    return store