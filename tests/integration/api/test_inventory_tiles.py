"""Inventory routes and TiTiler mount smoke tests (Step 1 I4/I5, R1)."""

from __future__ import annotations

import morecantile
import pytest
from fastapi.testclient import TestClient

from geoaicubes.api.app import create_app
from geoaicubes.api.schemas.inventory import ZarrInventoryList, ZarrStoreInventory
from geoaicubes.config import get_storage_settings
from geoaicubes.io.inventory import discover_store_ids

_DEMO_STORE = "GeoDataCube_cobertes-sol-v1r0-2023.zarr"
_GOLDEN_URI = (
    "s3://data/GEODATACUBE_ZARR_openEO/GeoDataCube_cobertes-sol-v1r0-2023.zarr/"
)
_STORE_FIELD_NAMES = frozenset(ZarrStoreInventory.model_fields.keys())


def _in_scope_store_ids() -> list[str]:
    settings = get_storage_settings()
    root = settings.local_zarr_root()
    if not root.is_dir():
        pytest.skip(f"Demo Zarr root not found: {root}")
    ids = discover_store_ids(settings)
    if not ids:
        pytest.skip(f"No *.zarr stores under {root}")
    return ids


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app())


def _assert_store_schema_shape(store: dict) -> ZarrStoreInventory:
    """Every list/detail store exposes the full D2 inventory contract."""
    assert set(store.keys()) == _STORE_FIELD_NAMES
    parsed = ZarrStoreInventory.model_validate(store)
    if parsed.status == "ok":
        assert parsed.error is None
        assert parsed.dims
        assert parsed.variables
    else:
        assert parsed.error
        assert not parsed.dims
        assert not parsed.variables
    return parsed


def test_inventory_lists_all_in_scope_zarr_names(client: TestClient) -> None:
    expected_ids = _in_scope_store_ids()
    list_resp = client.get("/api/v1/inventory/zarr")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    listing = ZarrInventoryList.model_validate(payload)
    assert listing.count == len(listing.stores)
    assert listing.count == len(expected_ids)

    api_ids = [store.id for store in listing.stores]
    assert api_ids == sorted(expected_ids)
    for store in payload["stores"]:
        _assert_store_schema_shape(store)


def test_inventory_golden_store_schema_fields(client: TestClient) -> None:
    expected_ids = _in_scope_store_ids()
    if _DEMO_STORE not in expected_ids:
        pytest.skip(f"Golden store not on disk: {_DEMO_STORE}")

    detail_resp = client.get(f"/api/v1/inventory/zarr/{_DEMO_STORE}")
    assert detail_resp.status_code == 200
    store = detail_resp.json()
    parsed = _assert_store_schema_shape(store)

    assert parsed.id == _DEMO_STORE
    assert parsed.uri == _GOLDEN_URI
    golden_path = (
        "data/GEODATACUBE_ZARR_openEO/GeoDataCube_cobertes-sol-v1r0-2023.zarr/"
    )
    assert parsed.path == golden_path
    assert parsed.status == "ok"
    assert parsed.dims == ["y", "x"]
    assert parsed.crs == "EPSG:25831"
    assert parsed.extent is not None
    assert parsed.extent.crs == "EPSG:25831"
    assert len(parsed.extent.bbox) == 4
    assert parsed.time is None

    assert len(parsed.variables) == 1
    variable = parsed.variables[0]
    assert variable.name == "data"
    assert variable.dtype == "uint8"
    assert variable.shape == [19600, 32000]

    assert "data" in parsed.nodata
    assert "data" in parsed.chunks
    assert parsed.chunks["data"]["y"] == 512
    assert parsed.chunks["data"]["x"] == 512

    assert "data" in parsed.render_capabilities
    cob_cap = parsed.render_capabilities["data"]
    assert cob_cap.defaults.mode == "categorical"
    assert cob_cap.primary is True

    template = parsed.tile_url_template.get("data", "")
    assert template.startswith("/tiles/zarr/")
    assert "variable=data" in template


def test_inventory_unknown_store_returns_404(client: TestClient) -> None:
    missing = client.get("/api/v1/inventory/zarr/does-not-exist.zarr")
    assert missing.status_code == 404


def test_zarr_tile_png_ok(client: TestClient) -> None:
    in_scope = _in_scope_store_ids()
    if _DEMO_STORE not in in_scope:
        pytest.skip(f"Golden store not on disk: {_DEMO_STORE}")

    detail = client.get(f"/api/v1/inventory/zarr/{_DEMO_STORE}").json()
    query = detail["tile_url_template"]["data"].split("?", 1)[1]

    tilejson = client.get(f"/tiles/zarr/WebMercatorQuad/tilejson.json?{query}")
    assert tilejson.status_code == 200
    body = tilejson.json()
    center = body["center"]
    z = body["minzoom"]

    tms = morecantile.tms.get("WebMercatorQuad")
    tile = tms.tile(center[0], center[1], z)
    tile_url = (
        f"/tiles/zarr/tiles/WebMercatorQuad/{tile.z}/{tile.x}/{tile.y}.png?{query}"
    )
    tile_resp = client.get(tile_url)
    assert tile_resp.status_code == 200
    assert tile_resp.headers["content-type"] == "image/png"
    assert len(tile_resp.content) > 100