"""GeoAICubes processing core — shared by CLI, API, notebooks, and benchmarks."""

from geoaicubes.config import DemoConfig, load_demo_config
from geoaicubes.logging_config import configure_logging, get_logger

__version__ = "0.1.0"
__all__ = [
    "DemoConfig",
    "__version__",
    "configure_logging",
    "get_logger",
    "load_demo_config",
]