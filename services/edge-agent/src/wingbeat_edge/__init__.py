"""Edge agent: audio capture, speech guard, DSP and MQTT uplink for Wingbeat sensors."""

from importlib.metadata import version

__all__ = ["__version__"]

__version__: str = version("wingbeat-edge-agent")
