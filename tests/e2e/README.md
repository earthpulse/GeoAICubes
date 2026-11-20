# Tests

## Automated (pytest)

```bash
make check    # or: uv run pytest
```

Smoke tests live next to this file (`test_health.py`). UI workflow reports stay under `user-reports/` (gitignored).

## Workflow test (UI)

```text
Terminal:  make up    # keep running
Cursor:    /test      # one UI check + one screenshot
```

The agent uses `curl` and the **Cursor browser MCP** (no Playwright).

- Scenario: [`scenarios/ui.md`](scenarios/ui.md)
- Catalog: [`catalog.yaml`](catalog.yaml)
- Report: `user-reports/YYYY-MM-DD-ui.md`
- Screenshot: `user-reports/screenshots/YYYY-MM-DD-ui.png`