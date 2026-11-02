"""Read-only public API and live event stream for Wingbeat."""

from importlib.metadata import version

__all__ = ["__version__"]

__version__: str = version("wingbeat-api")
