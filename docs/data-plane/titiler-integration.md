# ADR D3 — TiTiler integration (Step 1)

| Field | Value |
|-------|--------|
| Status | **Accepted** (Wave 1 design) |
| Date | 2026-11-20 |
| Deliverable trace | Step 1 → D1.1 inventory + map preview; enables D2.1 viewer tiles later |
| Implements in | `src/geoaicubes/api/tiles.py` (Wave 3, I5) |

## Context

Step 1 must serve **PNG map tiles** from GeoDataCube **Zarr** stores already exposed as `s3://…` URIs via MinIO ([`docs/demo-config.md`](../demo-config.md)). The stack already depends on **`titiler-xarray[full]`** (`pyproject.toml`). The viewer talks **only to the API**; inventory responses must include **tile URL templates** with stable query parameters.

Two integration options were in scope:

1. **Single host** — mount `titiler-xarray` on the GeoAICubes FastAPI app (sub-app or `TilerFactory` router).
2. **Sidecar** — add a separate `titiler` Compose service (standalone `titiler.xarray.main:app`).

Program architecture requires **one Python processing core** and a **single API host** for the demo Compose topology (`references/implementation-roadmap.md` Step 0–1).

## Decision

**Mount `titiler-xarray` on the existing FastAPI API process** at a fixed path prefix. **Do not** add a dedicated TiTiler container in `deploy/docker-compose.yml`.

### Mount shape (implementation contract)

- Register the multidimensional `TilerFactory` from `titiler.xarray` (same extensions as upstream defaults: dataset metadata, validate) via `app.include_router(…, prefix="/tiles/zarr")`, with `router_prefix="/tiles/zarr"` on the factory so TileJSON and operation IDs resolve correctly.
- Expose only the **tiling surface** needed for Step 1 (tile, tilejson, info as required for smoke tests). Auxiliary routers (global TMS listing, algorithms, colormaps) stay optional; omit separate landing `/` and `/conformance` from the GeoAICubes OpenAPI unless needed for debugging.
- Apply **one GDAL / S3 environment** derived from `GEOAICUBES_STORAGE__*` (same layout as inventory I/O) inside the tile routes so `url=s3://data/GEODATACUBE_ZARR_openEO/...` resolves against MinIO in Compose.
- Keep CORS on the **parent** FastAPI app (`GEOAICUBES_CORS_ORIGINS`); do not run a second HTTP listener.

### Rejected: Compose sidecar

A standalone TiTiler service would:

- Duplicate **MinIO credentials, bucket layout, and CORS** configuration.
- Force the viewer or inventory to reference a **second origin** (or an extra reverse proxy), violating the “viewer → API only” boundary.
- Add a second image/healthcheck path for no gain on a **CPU-only demo** with modest concurrent tile traffic.

**Exception (out of scope):** A sidecar remains acceptable for **production hardening** (isolated scaling, different release cadence) after Step 1; it is not the Step 1 default.

## Rationale summary

| Criterion | FastAPI mount | Compose `titiler` service |
|-----------|---------------|---------------------------|
| Viewer boundary (API-only) | Templates use `{API}/tiles/zarr/...` | Needs proxy or second base URL |
| Shared storage config | Single `GEOAICUBES_STORAGE__*` | Duplicate env on two services |
| Compose complexity | `api` only | Extra service + wiring |
| Dependency version lock | One process, one `uv.lock` | Must keep images in sync |
| Step 1 acceptance | Matches roadmap “API tile mount” | Valid but heavier |

## Tile HTTP contract

All tile requests are **GET**. Paths follow TiTiler 2.x xarray routes under the mount prefix.

### Path template

```text
GET /tiles/zarr/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}
```

| Path segment | Value (Step 1) |
|--------------|----------------|
| `tileMatrixSetId` | `WebMercatorQuad` (Leaflet default) |
| `z`, `x`, `y` | Standard XYZ tile indices |
| `format` | `png` (preferred; use when a mask is required) or `jpeg` |

### Query parameters (GeoAICubes contract)

Parameters below are what **inventory tile templates** MUST document and what the **viewer** MUST pass through unchanged unless noted.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | **Yes** | Dataset location. Step 1 uses percent-encoded `s3://{bucket}/{prefix}/{store}.zarr/` from inventory (`GEOAICUBES_STORAGE__*` mapping in `demo-config.md`). |
| `variable` | **Yes** | Xarray variable name to render (one band or single-valued field). |
| `rescale` | Recommended | Min/max stretch per rendered band, TiTiler form `min,max`. Repeat the parameter once per band when the variable is multi-band. Examples: `rescale=0,3000` (reflectance), `rescale=0,255` (byte classified preview). Omit only when defaults are documented per layer in inventory. |
| `sel` | Optional (time) | Xarray dimension selector(s), repeatable. For a **time index**, use `sel=time=<label>` where `<label>` is the coordinate value string from inventory (e.g. ISO-8601). Alternative TiTiler form: `sel=time=nearest::<label>`. Other dimensions (e.g. `level=…`) use the same `{dimension}={value}` pattern. |
| `colormap_name` | Optional | TiTiler colormap for categorical layers (e.g. `schwarzwald`). |
| `nodata` | Optional | Override nodata for preview. |

#### Inventory helper: `time_index`

The OpenAPI inventory schema may expose an optional integer **`time_index`** (0-based) on each layer for UI stepping. **It is not sent to TiTiler directly.** The API resolves it when building templates:

```text
time_index=i  →  sel=time=<inventory.times[i]>
```

If the store has no `time` dimension, omit `time_index` and any `sel` time clause.

### Example

```text
GET /tiles/zarr/tiles/WebMercatorQuad/10/512/384.png
  ?url=s3%3A%2F%2Fdata%2FGEODATACUBE_ZARR_openEO%2FGeodatacube_orto2024.zarr%2F
  &variable=band_1
  &rescale=0%2C3000
  &sel=time=2024-06-01T00%3A00%3A00
```

### TileJSON

For Leaflet `L.tileLayer`, inventory may also emit a **TileJSON** URL:

```text
GET /tiles/zarr/tiles/WebMercatorQuad/{z}/{x}/{y}.png?url=...&variable=...&rescale=...
```

(or the corresponding `/tiles/zarr/…/tilejson.json` endpoint with the same query string — implementation in I5 should prefer one style consistently in templates).

## Compose reference

`deploy/docker-compose.yml` keeps **one `api` service** on port `8000`. TiTiler runs in that container; no `titiler:` service. The API receives `GEOAICUBES_STORAGE__*` (and MinIO-related env) so mounted tile code and inventory share MinIO endpoint, bucket, and credentials.

## Consequences

- Wave 3 task **I5** implements `src/geoaicubes/api/tiles.py` and registers it from `create_app()`.
- Wave 3 task **I4** embeds tile templates using the query contract above.
- Integration smoke (**R2**): at least one demo Zarr returns a non-empty PNG via the mounted path.
- OpenAPI will list TiTiler routes under the `/tiles/zarr` prefix unless explicitly excluded from schema.

## Related docs

- [Demo configuration — MinIO URIs](../demo-config.md)
- [Step 1 implementation plan](../../tasks/step1/plan.md) (D3 → I5)
- Upstream: [TiTiler Xarray](https://developmentseed.org/titiler/)