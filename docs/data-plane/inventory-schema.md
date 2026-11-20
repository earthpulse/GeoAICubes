# Zarr inventory API schema (Step 1 — D2)

Design contract for **`GET /api/v1/inventory/zarr`** (list) and **`GET /api/v1/inventory/zarr/{id}`** (detail). Implementation: `src/geoaicubes/io/inventory.py` (I2) populates these shapes; HTTP routes (I4) return them via the Pydantic models in `src/geoaicubes/api/schemas/inventory.py`.

OpenAPI fragment: [`inventory.openapi.yaml`](inventory.openapi.yaml).

## Endpoints

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/api/v1/inventory/zarr` | [`ZarrInventoryList`](#zarrinventorylist) |
| `GET` | `/api/v1/inventory/zarr/{id}` | [`ZarrStoreInventory`](#zarrstoreinventory) |

`{id}` is the store [`id`](#id) (URL-safe; same as discovery key).

List enumeration must include **every** `*.zarr` under the configured root; a store with introspection failure still appears with `status: "error"`. The list endpoint always returns **200** when discovery succeeds (per-store errors are not elevated to HTTP 5xx).

## `ZarrInventoryList`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stores` | array of [`ZarrStoreInventory`](#zarrstoreinventory) | yes | One entry per discovered Zarr store |
| `count` | integer | yes | `len(stores)` (convenience for clients) |

## `ZarrStoreInventory`

Per-store record. Checklist fields match the table below exactly.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| [`id`](#id) | string | yes | Stable store identifier (typically `*.zarr` basename) |
| [`uri`](#uri) | string | yes | Canonical logical URI (`s3://…` in Compose; may mirror host layout in native dev) |
| [`path`](#path) | string | yes | Path used to open the store from the API host (filesystem or `s3://` URI) |
| [`status`](#status) | `"ok"` \| `"error"` | yes | Metadata introspection outcome for this store |
| [`error`](#error) | string \| null | yes | Human-readable failure message when `status` is `"error"`; `null` when `"ok"` |
| [`dims`](#dims) | string[] | yes | Dimension names for the store (union or primary grid order); `[]` on error |
| [`variables`](#variables) | [`InventoryVariable[]`](#inventoryvariable) | yes | Data variables with name, dtype, shape; `[]` on error |
| [`crs`](#crs) | string \| null | yes | CRS for the store grid (e.g. `EPSG:25831` or WKT); `null` if unknown or error |
| [`extent`](#extent) | [`InventoryExtent`](#inventoryextent) \| null | yes | Geographic bounds; `null` if unknown or error |
| [`time`](#time) | [`InventoryTime`](#inventorytime) \| null | no | Present when a time dimension exists; omit or `null` otherwise |
| [`nodata`](#nodata) | object | yes | Per-variable nodata; keys = variable names; `null` value if unset; `{}` on error |
| [`chunks`](#chunks) | object | yes | Per-variable Zarr chunking; see [chunks](#chunks); `{}` on error |
| [`tile_url_template`](#tile_url_template) | object | yes | Per **renderable** variable tile URL templates; see below; `{}` if none |

### `id`

Unique among stores in the demo root. Convention: directory name including `.zarr` suffix, e.g. `Geodatacube_orto2024.zarr`.

### `uri`

Logical location aligned with [`docs/demo-config.md`](../demo-config.md), e.g.  
`s3://data/GEODATACUBE_ZARR_openEO/Geodatacube_orto2024.zarr/`.

### `path`

Concrete open path on the API runtime: host-relative path in native dev, or the same `s3://` URI when using MinIO/s3fs in Compose.

### `status`

- `"ok"` — metadata read succeeded; spatial/time fields are best-effort but present when derivable.
- `"error"` — open or introspection failed; `error` is set; other fields are empty or `null` as documented.

### `error`

Non-empty string when `status` is `"error"`. Must be `null` when `status` is `"ok"`.

### `dims`

Ordered list of dimension names (e.g. `["time", "y", "x"]`). Sourced from Xarray/Zarr metadata without loading array values.

### `variables`

### `InventoryVariable`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Variable name in the Zarr group |
| `dtype` | string | yes | NumPy-style dtype string (e.g. `float32`, `uint8`) |
| `shape` | integer[] | yes | Length per dimension, same order as store `dims` where applicable |

### `crs`

Coordinate reference system for the primary spatial grid. Prefer EPSG codes when known.

### `extent`

### `InventoryExtent`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bbox` | number[4] | yes | `[minx, miny, maxx, maxy]` in `crs` axis order |
| `crs` | string | yes | CRS of the bbox (often same as store `crs`) |

### `time`

Optional. Include when the store has a time-like coordinate.

### `InventoryTime`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dim` | string | yes | Name of the time dimension |
| `values` | string[] \| null | no | ISO-8601 timestamps when small enough to serialize; `null` if omitted (large series) |
| `start` | string \| null | no | First timestamp (ISO-8601) |
| `end` | string \| null | no | Last timestamp (ISO-8601) |
| `count` | integer \| null | no | Length of the time dimension |

### `nodata`

Map **variable name → nodata value**. Use JSON `null` for the value when the variable has no nodata. Numeric nodata may be integer or float.

### `chunks`

Map **variable name → (dimension name → chunk size)**.

Example:

```json
"chunks": {
  "data": { "time": 1, "y": 512, "x": 512 }
}
```

### `tile_url_template`

Map **renderable variable name → URL template** for map clients (Leaflet). Only variables that TiTiler can serve as map tiles appear here.

Templates use RFC 6570-style placeholders or literal `{z}`, `{x}`, `{y}` for slippy tiles. Path is relative to the API origin unless absolute (Compose may proxy TiTiler under the API).

Example (illustrative — exact path finalized in I5/I4):

```json
"tile_url_template": {
  "data": "/tiles/zarr/{id}/{variable}/{z}/{x}/{y}.png"
}
```

## Example (`status: "ok"`)

See [`inventory.example.json`](inventory.example.json).

Optional filing snapshot from the same payload as a live list response: `make inventory-export` writes [`inventory-export.json`](inventory-export.json) (in-process I/O). With the API already running, use `uv run geoaicubes inventory-export --api-base http://localhost:8000`.

## Consumers

| Step | Component | Use |
|------|-----------|-----|
| I2 | `io/inventory.py` | Build `ZarrStoreInventory` dicts / models |
| I4 | `api/routes/inventory.py` | Expose list + detail; OpenAPI from Pydantic |
| D4 / I7 | `apps/viewer/` | IA: [`viewer-ia.md`](viewer-ia.md) — layer list, validation panel, Leaflet toggles, extent fit, optional time step |