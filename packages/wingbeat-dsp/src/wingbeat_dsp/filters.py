"""Band-pass and mains-hum filters (ROADMAP M2.3).

* **Band-pass**: a Butterworth band-pass from 250 to 2,500 Hz, as second-order sections (SOS)
  for numerical stability. The band holds wingbeat fundamentals (about 340-740 Hz, Kim et al.
  2021) and their first harmonics.
* **Mains-hum notch**: narrow IIR notches at the mains frequency (50 or 60 Hz) and its first
  harmonics. Only the lowest harmonics are notched, by default up to 250 Hz for 50 Hz mains and
  300 Hz for 60 Hz: higher harmonics fall on wingbeat fundamentals (550 Hz is both the 11th
  harmonic of 50 Hz and a typical *Culex* female), so notching them would remove the signal.
  The band-pass already attenuates everything below 250 Hz.

Filters are causal. :func:`apply` filters a whole signal from rest; :class:`StreamingFilter`
keeps the filter state between chunks and gives exactly the same output for any chunking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import numpy as np
from scipy.signal import butter, iirnotch, sosfilt, sosfilt_zi, tf2sos

from wingbeat_dsp.conditioning import TARGET_RATE_HZ

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "BAND_HIGH_HZ",
    "BAND_LOW_HZ",
    "StreamingFilter",
    "apply",
    "bandpass_sos",
    "cascade",
    "hum_notch_sos",
]

BAND_LOW_HZ: Final = 250.0
"""Lower edge of the wingbeat band."""

BAND_HIGH_HZ: Final = 2_500.0
"""Upper edge of the wingbeat band."""


def bandpass_sos(
    rate_hz: int = TARGET_RATE_HZ,
    *,
    low_hz: float = BAND_LOW_HZ,
    high_hz: float = BAND_HIGH_HZ,
    order: int = 4,
) -> NDArray[np.float64]:
    """Butterworth band-pass as second-order sections (``order`` per edge).

    Raises:
        ValueError: If the band is empty or reaches the Nyquist frequency.
    """
    if not 0 < low_hz < high_hz < rate_hz / 2:
        msg = f"need 0 < low < high < Nyquist, got {low_hz}, {high_hz} at {rate_hz} Hz"
        raise ValueError(msg)
    return np.asarray(
        butter(order, [low_hz, high_hz], btype="bandpass", fs=rate_hz, output="sos"),
        dtype=np.float64,
    )


def hum_notch_sos(
    mains_hz: float = 50.0,
    rate_hz: int = TARGET_RATE_HZ,
    *,
    harmonics: int = 5,
    quality: float = 30.0,
) -> NDArray[np.float64]:
    """Cascade of notches at ``mains_hz`` and its harmonics up to ``harmonics * mains_hz``.

    Args:
        mains_hz: Mains frequency, 50 or 60 Hz.
        rate_hz: Sample rate.
        harmonics: Number of harmonics to notch, the fundamental included.
        quality: Quality factor of each notch: centre frequency over -3 dB bandwidth.

    Raises:
        ValueError: If a notch would sit at or above the Nyquist frequency.
    """
    if harmonics < 1 or quality <= 0 or mains_hz <= 0:
        msg = "harmonics must be >= 1 and mains_hz and quality positive"
        raise ValueError(msg)
    if harmonics * mains_hz >= rate_hz / 2:
        msg = f"the {harmonics}th harmonic of {mains_hz} Hz is not below Nyquist ({rate_hz / 2} Hz)"
        raise ValueError(msg)
    sections = [
        tf2sos(*iirnotch(k * mains_hz, quality, fs=rate_hz)) for k in range(1, harmonics + 1)
    ]
    return np.asarray(np.vstack(sections), dtype=np.float64)


def cascade(*sos: NDArray[np.float64]) -> NDArray[np.float64]:
    """Join filters into one chain of second-order sections, applied in order."""
    return np.asarray(np.vstack(sos), dtype=np.float64)


def apply(sos: NDArray[np.float64], samples: ArrayLike) -> NDArray[np.float64]:
    """Filter a whole signal, starting from rest."""
    signal = np.asarray(samples, dtype=np.float64)
    if signal.size == 0:
        return signal
    return np.asarray(sosfilt(sos, signal), dtype=np.float64)


class StreamingFilter:
    """A causal SOS filter that keeps its state between chunks."""

    def __init__(self, sos: NDArray[np.float64]) -> None:
        """Start from rest."""
        self.sos = np.asarray(sos, dtype=np.float64)
        self._state = np.zeros_like(sosfilt_zi(self.sos))

    def process(self, chunk: ArrayLike) -> NDArray[np.float64]:
        """Filter one chunk, continuing from the previous one."""
        signal = np.asarray(chunk, dtype=np.float64)
        if signal.size == 0:
            return signal
        out, self._state = sosfilt(self.sos, signal, zi=self._state)
        return np.asarray(out, dtype=np.float64)

    def reset(self) -> None:
        """Return to rest, for example after a gap in the stream."""
        self._state = np.zeros_like(self._state)
