"""Stateful stream processing for Wingbeat: validation, enrichment, attribution, alerts."""

from importlib.metadata import version

__all__ = ["__version__"]

__version__: str = version("wingbeat-stream-processor")
