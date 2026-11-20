"""Unit tests for metadata-driven render capability inference."""

from __future__ import annotations

import pytest

from geoaicubes.config import get_storage_settings
from geoaicubes.io.inventory import open_dataset_for_tests
from geoaicubes.io.render import (
    infer_render_capability,
    infer_store_render_capabilities,
)


@pytest.fixture(scope="module")
def demo_ds():
    settings = get_storage_settings()
    root = settings.local_zarr_root()
    if not root.is_dir():
        pytest.skip(f"Demo Zarr root not found: {root}")
    store_id = "Geodatacube_orto2024.zarr"
    path = root / store_id
    if not path.is_dir():
        pytest.skip(f"Missing {store_id}")
    return open_dataset_for_tests(settings, store_id)


def test_orto_infers_named_rgb_bands(demo_ds) -> None:
    caps = infer_store_render_capabilities(demo_ds, None)
    demo_ds.close()
    cap = caps["data"]
    assert "rgb" in cap.modes
    assert cap.defaults.mode == "rgb"
    assert cap.defaults.sel["bands"] == ["RED", "GRN", "BLU"]
    assert cap.defaults.bidx == [1, 2, 3]


def test_cobertes_infers_categorical() -> None:
    settings = get_storage_settings()
    store_id = "GeoDataCube_cobertes-sol-v1r0-2023.zarr"
    path = settings.local_zarr_root() / store_id
    if not path.is_dir():
        pytest.skip("cobertes store missing")
    ds = open_dataset_for_tests(settings, store_id)
    cap = infer_render_capability(ds, "data", None)
    ds.close()
    assert cap is not None
    assert cap.defaults.mode == "categorical"
    assert cap.defaults.colormap
    assert len(cap.legend) > 0
