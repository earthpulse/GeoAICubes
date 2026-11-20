---
id: ui
category: ui
title: Viewer (Compose stack up)
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

With **`make up`** running, open the viewer and capture **one screenshot**.

## Operator prerequisite

**`make up`** with API healthy on `:8000`.

## Constants

| Name | Value |
|------|--------|
| UI URL | `http://localhost:5173/` |
| Screenshot | `tests/e2e/user-reports/screenshots/<date>-ui.png` |

## Steps

### S1 — Preflight `[http]`

- **Action:** `curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:5173/` and `curl -sf http://localhost:8000/health`
- **Expect (user-visible):** Both succeed (not 000).
- **Notes:** Blocker if down — run `make up`.

### S2 — Viewer `[browser]`

- **Action:** `browser_navigate` to UI URL (`position: "active"`). `browser_snapshot`; `browser_take_screenshot` → screenshot path above.
- **Expect (user-visible):** Title **GeoAICubes Viewer**; map placeholder; API health panel shows JSON or a clear error (not endless Loading…).

## Exit

- **Pass:** S1 and S2 pass.
- **Partial:** S1 pass, browser fails after one navigate retry — note URLs tried.