#!/usr/bin/env python3
"""Write docs/data-plane/inventory-export.json (Step 1 E3)."""

from __future__ import annotations

from geoaicubes.cli import DEFAULT_INVENTORY_EXPORT, inventory_export_command

if __name__ == "__main__":
    inventory_export_command(output=DEFAULT_INVENTORY_EXPORT, api_base=None)