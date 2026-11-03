"""Spectral estimation: Welch PSD, interpolated peaks and spectral flatness (ROADMAP M2.5).

* **Welch PSD** (Welch 1967): the mean of Hann-windowed periodograms of overlapping segments.
  Averaging lowers the variance of each bin, which the noise floor and flatness rely on.
* **Peak interpolation**: a parabola through the decibel values of the highest bin and its two
  neighbours gives the peak's position between bins (Smith & Serra 1987). With a Hann window
  the error is a small fraction of a bin, well under 1 Hz at 8 kHz with 1,024-sample segments
  (7.8 Hz bins).
* **Spectral flatness** (Wiener entropy; Johnston 1988): the geometric over the arithmetic mean
  of the PSD in a band, near 1 for white noise and near 0 for a pure tone. It separates a
  tonal wingbeat from broadband wind or rain.

References:
    Welch, P. (1967). The use of fast Fourier transform for the estimation of power spectra.
    IEEE Transactions on Audio and Electroacoustics, 15(2), 70-73.

    Smith, J. O. & Serra, X. (1987). PARSHL: an analysis/synthesis program for non-harmonic
    sounds based on a sinusoidal representation. Proceedings of the ICMC.

    Johnston, J. D. (1988). Transform coding of audio signals using perceptual noise criteria.
    IEEE Journal on Selected Areas in Communications, 6(2), 314-323.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from scipy.signal import welch

from wingbeat_dsp.conditioning import DEFAULT_FRAME_LENGTH, DEFAULT_HOP_LENGTH, TARGET_RATE_HZ
from wingbeat_dsp.filters import BAND_HIGH_HZ, BAND_LOW_HZ

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "Peak",
    "Spectrum",
    "dominant_peak",
    "interpolate_peak",
    "spectral_flatness",
    "welch_psd",
]

_TINY = 1e-300


@dataclass(frozen=True, slots=True)
class Spectrum:
    """A one-sided power spectral density.

    Attributes:
        frequencies_hz: Bin centre frequencies.
        psd: Power spectral density in units squared per hertz.
    """

    frequencies_hz: NDArray[np.float64]
    psd: NDArray[np.float64]

    @property
    def bin_width_hz(self) -> float:
        """Spacing of the bins."""
        return float(self.frequencies_hz[1] - self.frequencies_hz[0])

    def band(self, low_hz: float, high_hz: float) -> NDArray[np.bool_]:
        """Mask of the bins in ``[low_hz, high_hz]``."""
        return (self.frequencies_hz >= low_hz) & (self.frequencies_hz <= high_hz)


@dataclass(frozen=True, slots=True)
class Peak:
    """A spectral peak.

    Attributes:
        frequency_hz: Interpolated peak frequency.
        power_db: Interpolated peak level, dB re 1 unit squared per hertz.
        bin_index: Index of the highest bin.
    """

    frequency_hz: float
    power_db: float
    bin_index: int


def welch_psd(
    samples: ArrayLike,
    rate_hz: int = TARGET_RATE_HZ,
    *,
    segment_length: int = DEFAULT_FRAME_LENGTH,
    hop_length: int = DEFAULT_HOP_LENGTH,
) -> Spectrum:
    """Welch PSD with Hann-windowed segments, no detrending, density scaling.

    Raises:
        ValueError: If the signal is shorter than one segment.
    """
    signal = np.asarray(samples, dtype=np.float64)
    if signal.ndim != 1 or signal.size < segment_length:
        msg = f"need a 1-D signal of at least {segment_length} samples, got shape {signal.shape}"
        raise ValueError(msg)
    freqs, psd = welch(
        signal,
        fs=rate_hz,
        window="hann",
        nperseg=segment_length,
        noverlap=segment_length - hop_length,
        detrend=False,
        scaling="density",
    )
    return Spectrum(np.asarray(freqs, dtype=np.float64), np.asarray(psd, dtype=np.float64))


def interpolate_peak(values_db: NDArray[np.float64], index: int) -> tuple[float, float]:
    """Parabolic interpolation around bin ``index`` of a decibel spectrum.

    Returns:
        ``(offset, level)``: the peak's offset from ``index`` in bins, within [-0.5, 0.5], and
        its interpolated level. At the first or last bin the offset is 0.
    """
    if index <= 0 or index >= values_db.size - 1:
        return 0.0, float(values_db[index])
    alpha, beta, gamma = (float(v) for v in values_db[index - 1 : index + 2])
    denominator = alpha - 2 * beta + gamma
    if denominator >= 0:  # not a local maximum: keep the bin centre
        return 0.0, beta
    offset = 0.5 * (alpha - gamma) / denominator
    offset = min(max(offset, -0.5), 0.5)
    return offset, beta - 0.25 * (alpha - gamma) * offset


def dominant_peak(
    spectrum: Spectrum, *, low_hz: float = BAND_LOW_HZ, high_hz: float = BAND_HIGH_HZ
) -> Peak:
    """The highest peak in a band, interpolated between bins.

    Raises:
        ValueError: If the band holds no bins.
    """
    band = spectrum.band(low_hz, high_hz)
    if not band.any():
        msg = f"no bins between {low_hz} and {high_hz} Hz"
        raise ValueError(msg)
    levels = 10 * np.log10(np.maximum(spectrum.psd, _TINY))
    candidates = np.flatnonzero(band)
    index = int(candidates[np.argmax(levels[candidates])])
    offset, level = interpolate_peak(levels, index)
    frequency = float(spectrum.frequencies_hz[index]) + offset * spectrum.bin_width_hz
    return Peak(frequency_hz=frequency, power_db=level, bin_index=index)


def spectral_flatness(
    spectrum: Spectrum, *, low_hz: float = BAND_LOW_HZ, high_hz: float = BAND_HIGH_HZ
) -> float:
    """Geometric over arithmetic mean of the PSD in a band, in [0, 1]; ``nan`` for silence."""
    values = spectrum.psd[spectrum.band(low_hz, high_hz)]
    if values.size == 0:
        msg = f"no bins between {low_hz} and {high_hz} Hz"
        raise ValueError(msg)
    arithmetic = float(values.mean())
    if arithmetic == 0:
        return float("nan")
    geometric = float(np.exp(np.mean(np.log(np.maximum(values, _TINY)))))
    return min(1.0, geometric / arithmetic)
