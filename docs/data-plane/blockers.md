# Data-plane blockers (Step 1 → Step 2+)

| Field | Value |
|-------|-------|
| Task | Step 1 **F2** — log stores that fail **open** or **tile** |
| Last check | 2026-11-20 |
| Source command | `uv run geoaicubes inventory-list` |
| Tile probe | `TestClient` + inventory `tile_url_template` → `tilejson.json` + one PNG at `minzoom` / TileJSON center (local filesystem discovery) |

Step 1 inventory **always lists** every `*.zarr` under `data/GEODATACUBE_ZARR_openEO/`; per-store `status: "error"` is surfaced in the viewer. This file tracks issues that block **Step 2+** (benchmarks, full viewer preview, D1.2 library paths, Compose demo).

## Inventory open (`status`)

| Store | `status` | Notes |
|-------|----------|-------|
| All 6 stores under `GEODATACUBE_ZARR_openEO/` | `ok` | Metadata introspection succeeds; no `status: "error"` entries on last run (`count`: 6). |

**Store IDs (all `ok`):**

- `GeoDataCube_cobertes-sol-v1r0-2023.zarr`
- `Geodatacube_S22024_2025.zarr`
- `Geodatacube_nDSM2024.zarr`
- `Geodatacube_nDSM2025.zarr`
- `Geodatacube_orto2024.zarr`
- `Geodatacube_orto2025.zarr`

## TiTiler map tiles (Step 1 viewer preview)

Probe uses templates from inventory (including `coord_crs` where CRS is known). **1 / 6** stores returned a PNG tile (>100 bytes) on the golden smoke tile.

| Store | Inventory CRS | Tile result | Failure class | Step 2+ impact |
|-------|---------------|-------------|---------------|----------------|
| `GeoDataCube_cobertes-sol-v1r0-2023.zarr` | EPSG:25831 | **OK** (PNG ~17 KB) | — | Use as **golden** demo layer for viewer/e2e and D1.3 baselines. |
| `Geodatacube_nDSM2024.zarr` | EPSG:25831 | **500** | **EngineeringCRS** — Zarr `spatial_ref` WKT resolves as PROJ `EngineeringCRS` (“ETRS89 / UTM zone 31N”); rio-tiler cannot warp **EPSG:3857 ↔ EngineeringCRS** even with `coord_crs=EPSG:25831` in the template. | Fix CRS in source assets or force EPSG in reader/TiTiler path; until then **no map preview** for nDSM. |
| `Geodatacube_nDSM2025.zarr` | EPSG:25831 | **500** | Same **EngineeringCRS** issue as nDSM2024. | Same as nDSM2024. |
| `Geodatacube_orto2024.zarr` | EPSG:25831 | **500** | **MaxArraySizeError** — multi-band `data` `(bands, y, x)`; rio-tiler tried to load `(4, 53877, 112787)` for one tile (band dimension not sliced). | Need `sel=band=…` (or RGB composite convention) in tile URL + inventory templates; ties to D1.3 limits. |
| `Geodatacube_orto2025.zarr` | EPSG:25831 | **500** | Same **MaxArraySizeError** / band stack as orto2024. | Same as orto2024. |
| `Geodatacube_S22024_2025.zarr` | EPSG:32631 | **400** | PNG encode — multi-dimensional tile slice `(10, 256, 256)` (time × band stack) not reduced to 2D raster. | Need explicit `sel=` for `time` and `band` (templates only set first `time` today); viewer time stepper must refresh tile URL. |

### Error excerpts (for ICGC / asset owners)

**EngineeringCRS (nDSM):**

```text
CPLE_NotSupportedError: Cannot find coordinate operations from 'EPSG:3857' to … "type": "EngineeringCRS", "name": "ETRS89 / UTM zone 31N" …
```

**Orto stack size:**

```text
MaxArraySizeError: Maximum array limit 1000000000 reached, trying to put DataArray of (4, 53877, 112787) in memory.
```

**S2 multi-band/time:**

```text
Could not encode array of shape (10,256,256) and of datatype `uint8` using PNG driver
```

## Cross-cutting (not per-store)

| Topic | Blocker / follow-up |
|-------|---------------------|
| **Compose / S3** | Compose API uses **filesystem** discovery on `/data/GEODATACUBE_ZARR_openEO` (in-place bind mount; no `mc` copy). Pure `DISCOVERY_MODE=s3` listing stays empty until objects exist under the bucket prefix — optional follow-up if we need S3-only reads without the shared mount. |
| **CRS mismatch** | Inventory reports EPSG from WKT aliases (`extract_crs`); TiTiler still reads raw WKT from the dataset → treat **tile CRS** as authoritative for preview until assets or I/O normalize CRS. |
| **Step 1 acceptance** | Discovery viewer can ship with **cobertes** as the proven tile layer; other layers remain listable with metadata but **validation findings** for tiles (per `viewer-ia.md`). |
| **D1.3** | Orto + S2 failures imply export/request limits and dimension slicing must be designed before Step 2 library/API heavy reads. |

## Regenerate this log

```bash
uv run geoaicubes inventory-list | jq '[.stores[] | {id, status, error, crs, templates: (.tile_url_template | keys)}]'
uv run pytest tests/integration/api/test_inventory_tiles.py -q   # golden store tile smoke
```

Update the tables above when adding Zarrs under `GEODATACUBE_ZARR_openEO/` or after fixing CRS, band selection, or TiTiler configuration.