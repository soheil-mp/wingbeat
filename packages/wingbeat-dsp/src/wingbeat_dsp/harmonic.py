"""Harmonic fundamental-frequency estimators with an octave-error guard (ROADMAP M2.6).

A flying mosquito's tone is a harmonic series: the wingbeat fundamental *f0* and its integer
multiples (Kim et al. 2021). Two classical estimators search *f0* over a grid of candidates and
sample the amplitude spectrum ``A`` (the square root of the PSD) at the candidate's harmonics:

* **Harmonic sum** (HSS; Hermes 1988): ``sum_k A(k * f0)``. Robust when the fundamental is weak
  or missing.
* **Harmonic product** (HPS; Schroeder 1968): ``prod_k A(k * f0)``, evaluated as a sum of
  logarithms. Sharp, but a single missing harmonic pulls it down.

Both use the first ``n_harmonics`` multiples below ``max_harmonic_hz``. The best candidate on a
0.25 Hz grid is then refined from the spectrum itself: each harmonic's interpolated peak near
``k * f0`` gives ``peak / k``, and the refined *f0* is their amplitude-weighted mean. Sampling the
amplitude spectrum between bins biases the grid search by up to about 1.5 Hz; the refinement
brings clean tones to well under 1 Hz.

**Octave-error guard.** Harmonic estimators confuse octaves. The harmonic product tends to pick
twice the true *f0* when the fundamental is weak; the harmonic sum tends to pick half of it
when there are few harmonics, because the sub-octave's harmonics include all the real ones.
The guard uses the odd multiples of a candidate: for a genuine *f0* they carry energy (the
fundamental, the third harmonic), while the odd multiples of ``f0 / 2`` hold only noise. It
doubles a candidate whose strongest odd multiple is below ``octave_ratio`` (-20 dB) of its
strongest even multiple, and halves one whose half's odd multiples reach that ratio. A real
series whose first and third harmonics are both more than 20 dB below the second is therefore
read an octave high; that ambiguity is inherent to the signal.

References:
    Schroeder, M. R. (1968). Period histogram and product spectrum: new methods for
    fundamental-frequency measurement. JASA, 43(4), 829-834.

    Hermes, D. J. (1988). Measurement of pitch by subharmonic summation. JASA, 83(1), 257-264.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from wingbeat_dsp.spectral import dominant_peak, interpolate_peak

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from wingbeat_dsp.spectral import Spectrum

__all__ = ["F0Estimate", "HarmonicConfig", "Method", "estimate_f0", "harmonic_power_fraction"]

_GRID_STEP_HZ: Final = 0.25
_FLOOR: Final = 1e-12


class Method(enum.StrEnum):
    """Which harmonic estimator to use."""

    SUM = "harmonic-sum"
    PRODUCT = "harmonic-product"


@dataclass(frozen=True, slots=True)
class HarmonicConfig:
    """Search range and parameters of the harmonic estimators.

    Attributes:
        f0_min_hz: Lowest candidate fundamental.
        f0_max_hz: Highest candidate fundamental.
        n_harmonics: Harmonics per candidate, the fundamental included.
        max_harmonic_hz: Harmonics above this frequency are not used.
        octave_ratio: Amplitude ratio (0.1 is -20 dB) below which odd harmonics count as absent
            in the octave guard; at 10 dB SNR the noise floor sits near 0.02-0.05.
    """

    f0_min_hz: float = 250.0
    f0_max_hz: float = 1_250.0
    n_harmonics: int = 5
    max_harmonic_hz: float = 3_500.0
    octave_ratio: float = 0.1


@dataclass(frozen=True, slots=True)
class F0Estimate:
    """An estimate of the fundamental frequency.

    Attributes:
        f0_hz: Estimated fundamental.
        method: Estimator that produced it.
        octave_corrected: Whether the guard halved the first choice.
        harmonic_power_fraction: Share of the in-band power near the estimate's harmonics.
    """

    f0_hz: float
    method: Method
    octave_corrected: bool
    harmonic_power_fraction: float


def _amplitude_at(spectrum: Spectrum, freqs_hz: NDArray[np.float64]) -> NDArray[np.float64]:
    amplitude = np.sqrt(np.maximum(spectrum.psd, 0.0))
    return np.asarray(np.interp(freqs_hz, spectrum.frequencies_hz, amplitude), dtype=np.float64)


def _harmonics(
    f0: NDArray[np.float64], config: HarmonicConfig
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    k = np.arange(1, config.n_harmonics + 1)
    freqs = f0[:, np.newaxis] * k[np.newaxis, :]
    return freqs, freqs <= config.max_harmonic_hz


def _salience(
    spectrum: Spectrum, f0: NDArray[np.float64], config: HarmonicConfig, method: Method
) -> NDArray[np.float64]:
    freqs, used = _harmonics(f0, config)
    amplitude = _amplitude_at(spectrum, freqs)
    if method is Method.SUM:
        return np.where(used, amplitude, 0.0).sum(axis=1)
    peak = max(float(np.sqrt(spectrum.psd.max())), _FLOOR)
    logs = np.log(np.maximum(amplitude / peak, _FLOOR))
    # Mean rather than sum, so candidates with fewer usable harmonics are not favoured.
    return np.where(used, logs, 0.0).sum(axis=1) / np.maximum(used.sum(axis=1), 1)


def _peak_amplitude(spectrum: Spectrum, freqs: list[float]) -> float:
    """Largest amplitude at the given frequencies (0 for none)."""
    return float(_amplitude_at(spectrum, np.asarray(freqs)).max()) if freqs else 0.0


def _odd_and_even(f0: float, config: HarmonicConfig) -> tuple[list[float], list[float]]:
    """Odd and even multiples of ``f0`` up to ``max_harmonic_hz`` (at most 2 * n_harmonics)."""
    multiples = [
        k * f0 for k in range(1, 2 * config.n_harmonics + 1) if k * f0 <= config.max_harmonic_hz
    ]
    return multiples[0::2], multiples[1::2]


def _octave_guard(spectrum: Spectrum, f0: float, config: HarmonicConfig) -> tuple[float, bool]:
    """Move ``f0`` by octaves until its odd harmonics are present and those of ``f0/2`` are not.

    Each side is represented by its strongest harmonic, so harmonics that hold only noise do not
    dilute the comparison.

    * Too low: if the strongest odd multiple of ``f0`` is weaker than ``octave_ratio`` times the
      strongest even multiple, the series really starts at ``2 f0``.
    * Too high: if the strongest odd multiple of ``f0/2`` reaches ``octave_ratio`` times the
      strongest multiple of ``f0``, the series really starts at ``f0/2``.
    """
    corrected = False
    while 2 * f0 <= config.f0_max_hz:
        odd, even = _odd_and_even(f0, config)
        even_level = _peak_amplitude(spectrum, even)
        if even_level <= 0 or _peak_amplitude(spectrum, odd) >= config.octave_ratio * even_level:
            break
        f0, corrected = 2 * f0, True
    while f0 / 2 >= config.f0_min_hz:
        half_odd, own = _odd_and_even(f0 / 2, config)
        own_level = _peak_amplitude(spectrum, own)
        if own_level <= 0 or _peak_amplitude(spectrum, half_odd) < config.octave_ratio * own_level:
            break
        f0, corrected = f0 / 2, True
    return f0, corrected


def _refine(spectrum: Spectrum, f0: float, config: HarmonicConfig) -> float:
    """Amplitude-weighted mean of ``peak_k / k`` over the harmonics of ``f0``."""
    width = 1.5 * spectrum.bin_width_hz
    estimates, weights = [], []
    for k in range(1, config.n_harmonics + 1):
        centre = k * f0
        if centre + width > min(config.max_harmonic_hz, float(spectrum.frequencies_hz[-1])):
            break
        peak = dominant_peak(spectrum, low_hz=centre - width, high_hz=centre + width)
        estimates.append(peak.frequency_hz / k)
        weights.append(10 ** (peak.power_db / 20))
    if not estimates or sum(weights) == 0:
        return f0
    return float(np.average(estimates, weights=weights))


def harmonic_power_fraction(
    spectrum: Spectrum, f0_hz: float, config: HarmonicConfig | None = None
) -> float:
    """Share of the band's power within two bins of the harmonics of ``f0_hz``.

    The band runs from ``f0_min_hz`` to ``max_harmonic_hz``. The share is near 1 for a clean
    harmonic series and small for noise.
    """
    cfg = config or HarmonicConfig()
    band = spectrum.band(cfg.f0_min_hz, cfg.max_harmonic_hz)
    total = float(spectrum.psd[band].sum())
    if total == 0:
        return 0.0
    near = np.zeros_like(band)
    width = 2 * spectrum.bin_width_hz
    for k in range(1, cfg.n_harmonics + 1):
        if k * f0_hz <= cfg.max_harmonic_hz:
            near |= np.abs(spectrum.frequencies_hz - k * f0_hz) <= width
    return float(spectrum.psd[band & near].sum()) / total


def estimate_f0(
    spectrum: Spectrum, method: Method = Method.SUM, config: HarmonicConfig | None = None
) -> F0Estimate:
    """Estimate the wingbeat fundamental from a spectrum.

    Raises:
        ValueError: If the search range is empty.
    """
    cfg = config or HarmonicConfig()
    if not 0 < cfg.f0_min_hz < cfg.f0_max_hz or cfg.n_harmonics < 1:
        msg = "need 0 < f0_min_hz < f0_max_hz and n_harmonics >= 1"
        raise ValueError(msg)
    grid = np.arange(cfg.f0_min_hz, cfg.f0_max_hz + _GRID_STEP_HZ / 2, _GRID_STEP_HZ)
    salience = _salience(spectrum, grid, cfg, method)
    best = int(np.argmax(salience))
    offset, _ = interpolate_peak(salience, best)
    f0 = float(grid[best] + offset * _GRID_STEP_HZ)
    f0, corrected = _octave_guard(spectrum, f0, cfg)
    f0 = _refine(spectrum, f0, cfg)
    return F0Estimate(
        f0_hz=f0,
        method=method,
        octave_corrected=corrected,
        harmonic_power_fraction=harmonic_power_fraction(spectrum, f0, cfg),
    )
