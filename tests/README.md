# Tests layout

| Path | Runner | Purpose |
|------|--------|---------|
| `tests/unit/` | `pytest` | Fast unit tests (open Zarr via `geoaicubes.io.inventory.open_dataset_for_tests`) |
| `tests/integration/` | `pytest` | API and stack integration (e.g. `TestClient`) |
| `tests/e2e/` | Cursor `/test` | AI-driven user workflow (catalog, scenarios, browser) |

## pytest (CI and local)

```bash
make test     # integration + unit only
make check    # ruff + format check + make test
```

`pytest` does **not** collect under `tests/e2e/` (see `[tool.pytest.ini_options]` in `pyproject.toml`).

## User workflow (e2e)

```text
Terminal:  make up    # keep running
Cursor:    /test      # one UI check + one screenshot
```

Details: [`tests/e2e/README.md`](e2e/README.md) · skill [`.cursor/skills/user-testing/SKILL.md`](../.cursor/skills/user-testing/SKILL.md)