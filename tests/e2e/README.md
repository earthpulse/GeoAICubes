# E2E — user workflow (`/test`)

Cursor agent checks with browser MCP (not collected by pytest).

## Layout

| Path | Role |
|------|------|
| `catalog.yaml` | Categories and scenario ids |
| `categories/` | Story tables per category |
| `scenarios/` | Step-by-step scripts |
| `user-reports/` | Run reports and screenshots (gitignored) |

## pytest (separate)

```bash
make test     # tests/integration + tests/unit
make check    # lint, format, make test
```

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