"""Shared settings, logging and telemetry helpers for Wingbeat services."""

from importlib.metadata import version

__all__ = ["__version__"]

__version__: str = version("wingbeat-common")
