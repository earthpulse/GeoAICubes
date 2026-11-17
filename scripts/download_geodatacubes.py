#!/usr/bin/env python3
"""Compatibility shim — use fetch_datacloud.py instead."""

from fetch_datacloud import main

if __name__ == "__main__":
    raise SystemExit(main())