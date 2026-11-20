---
id: ui
category: ui
title: Step 1 discovery viewer (Compose)
persona: Demo operator with make up running
stories:
  - UI-1
entry_doc: Makefile
requires:
  - compose-running
services:
  compose: prereq
teardown: []
ui_url: http://localhost:5173/
---

## Goal

With **`make up`** running, exercise the **Step 1** discovery viewer: **layer list** from inventory, **Leaflet map tiles** from API TiTiler templates, and **validation errors** surfaced inline (per-store `status: "error"`). Capture **one screenshot** after map preview is enabled.

Contract: API inventory shapes (`src/geoaicubes/api/schemas/inventory.py`) and viewer `apps/viewer/README.md`.

## Operator prerequisite

**`make up`** with API healthy on `:8000` and Zarr tree under `data/GEODATACUBE_ZARR_openEO/` (see `README.md` and `config/.env.example`).

## Constants

| Name | Value |
|------|--------|
| UI URL | `http://localhost:5173/` |
| API base | `http://localhost:8000` |
| Health | `http://localhost:8000/health` |
| Inventory | `http://localhost:8000/api/v1/inventory/zarr` |
| Screenshot | `tests/e2e/user-reports/screenshots/<date>-ui.png` |
| Report | `tests/e2e/user-reports/<date>-ui.md` |

## Steps

### S1 — Preflight `[http]`

- **Action:** `curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:5173/`; `curl -sf http://localhost:8000/health`; `curl -sf http://localhost:8000/api/v1/inventory/zarr | jq -e '.stores | length >= 1'`
- **Expect:** UI **200**; health JSON with `status: ok`; inventory **200** with non-empty `stores` array.
- **Notes:** Blocker if down — run `make up`. If inventory is empty, stop and fix data plane (Step 1 R4) before browser steps.

### S2 — Shell and inventory load `[browser]`

- **Action:** `browser_navigate` to UI URL (`position: "active"`). Wait until header pills leave loading state (`API ok`, inventory count not `Loading inventory…`). `browser_snapshot`.
- **Expect (user-visible):** Title **GeoAICubes Viewer**; tagline **Zarr discovery — map layers via API only**; **Layers** and **Metadata** headings in sidebar; Leaflet map region (`aria-label="Leaflet map"`) — **no** “Map placeholder” copy.
- **Notes:** One navigate retry allowed if first load is `about:blank`.

### S3 — Layer list `[browser]`

- **Action:** From snapshot, read sidebar **Layers** section. Click the first row whose badge is **ok** (or any row if all are error). Re-snapshot.
- **Expect (user-visible):**
  - ≥1 layer row with store id label and **ok** or **error** badge.
  - Header inventory pill like `N stores (X ok, Y error)` matching API list counts (approximate).
  - For a selected **ok** row: **Metadata** panel shows store fields (URI, status), not only “Select a store from the layer list.”
  - Rows with **error** badge (if any): truncated red hint under the row; visibility checkbox absent or disabled for that store.
- **Notes:** List must remain usable when some stores fail — no whole-page crash on mixed ok/error inventory.

### S4 — Map tiles `[http]` + `[browser]`

- **Action (http):** From S1 inventory JSON, pick the first store with `status === "ok"` and a non-empty `tile_url_template`. Resolve one template (prepend `http://localhost:8000` if relative). Substitute `{z}=10`, `{x}=512`, `{y}=512` (adjust if template uses different zoom). `curl -sf -o /dev/null -w "%{http_code} %{content_type}\n" "<tile-url>"`.
- **Expect (http):** **200** and `image/png` (or `image/jpeg`).
- **Action (browser):** On the same store’s renderable variable row, enable the **visibility** checkbox. Optionally click **Fit extent (selected)** if enabled. `browser_take_screenshot` → screenshot path above.
- **Expect (user-visible):** Map shows OSM basemap; after toggle, overlay loads without breaking the map (no blank tile pane). Screenshot documents sidebar + map with at least one layer toggled on.
- **Notes:** If no ok store has templates, fail S4 and note blockers in the report. TiTiler is mounted on the API at `/tiles/zarr` — tile URLs must stay under `localhost:8000`, not MinIO.

### S5 — Validation errors `[browser]` + `[http]`

- **Action (http):** `curl -sf http://localhost:8000/api/v1/inventory/zarr | jq '[.stores[] | select(.status == "error")] | length'` → `ERR_COUNT`.
- **Action (browser):** If `ERR_COUNT > 0`, select each **error** row once; snapshot metadata.
- **Expect:**
  - **`ERR_COUNT > 0`:** Layer list shows **error** badges; row shows truncated `error` text; **Metadata** shows full `error` in an alert (`role="alert"`). Tile visibility remains disabled for that store.
  - **`ERR_COUNT == 0`:** Record **N/A — no per-store errors in inventory** in the report; S5 still passes (validation UI not exercisable without a failing store).
- **Notes:** Page-level banner **Inventory request failed** is a *fetch* failure (5xx/network), distinct from per-store validation — do not conflate in the report. A forced-bad store id in fixtures is optional; live disk inventory may have zero errors.

## Exit

- **Pass:** S1–S4 pass; S5 pass (or N/A with `ERR_COUNT == 0` documented).
- **Partial:** S1 pass, browser fails after one navigate retry — note URLs tried and last inventory `jq` summary.
- **Fail:** Empty inventory, no tile template on any ok store, or tile `curl` not 200/png.

## Report checklist

Include in `user-reports/<date>-ui.md`:

| Step | Modality | Result | User-visible outcome |
|------|----------|--------|----------------------|
| S1 | http | | |
| S2 | browser | | |
| S3 | browser | | |
| S4 | http+browser | | Tile store id + variable; curl status; screenshot path |
| S5 | http+browser | | `ERR_COUNT`; error row/metadata if any |