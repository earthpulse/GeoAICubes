"""Shared logging setup for CLI, API, and library entry points.

Format (stderr): ``%(asctime)s | %(levelname)s | %(name)s | %(message)s``
(``%Y-%m-%d %H:%M:%S``). Level from ``GEOAICUBES_LOG_LEVEL`` (default ``INFO``).
See ``README.md`` (logging) and ``GEOAICUBES_LOG_LEVEL`` in ``config/.env.example``.
"""

from __future__ import annotations

import logging
import os
import sys

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CONFIGURED = False


def _parse_level(raw: str | None) -> int:
    if not raw or not raw.strip():
        return logging.INFO
    name = raw.strip().upper()
    level = logging.getLevelNamesMapping().get(name)
    if level is None:
        return logging.INFO
    return level


def configure_logging(*, level: int | str | None = None, force: bool = False) -> None:
    """
    Configure root logging once with a consistent format across CLI and API.

    Level defaults to ``GEOAICUBES_LOG_LEVEL`` (``INFO`` when unset).
    """
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    if isinstance(level, str):
        resolved = _parse_level(level)
    elif level is not None:
        resolved = level
    else:
        resolved = _parse_level(os.environ.get("GEOAICUBES_LOG_LEVEL"))

    logging.basicConfig(
        level=resolved,
        format=_LOG_FORMAT,
        datefmt=_LOG_DATE_FORMAT,
        stream=sys.stderr,
        force=force or not _CONFIGURED,
    )
    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced logger, ensuring :func:`configure_logging` ran first."""
    configure_logging()
    return logging.getLogger(name or "geoaicubes")
