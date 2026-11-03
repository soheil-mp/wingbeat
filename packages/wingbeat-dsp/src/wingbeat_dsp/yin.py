"""YIN time-domain fundamental estimator and estimator agreement (ROADMAP M2.7).

YIN (de Cheveigné & Kawahara 2002) works on the waveform rather than the spectrum, so it fails in
different ways from the harmonic estimators and makes a useful cross-check:

1. Difference function ``d(tau) = sum_j (x[j] - x[j + tau])^2`` over a fixed window.
2. Cumulative mean normalised difference ``d'(tau) = d(tau) / ((1 / tau) * sum_{1..tau} d)``,
   with ``d'(0) = 1``.
3. The first ``tau`` in range where ``d'`` drops below ``threshold`` (0.1 in the paper), followed
   to its local minimum; if none drops below, the global minimum.
4. Parabolic interpolation around that minimum.

At 8 kHz a 550 Hz period is only about 14.5 samples, so sub-sample interpolation errors become
hertz. The frame is therefore upsampled by ``upsample`` (4 by default) with a polyphase filter
before step 1, which keeps the error on clean tones well under 1 Hz.

The value ``d'`` at the chosen lag is the *aperiodicity*: near 0 for a periodic signal, near 1 for
noise.

:func:`agreement` scores how well two estimates agree, in cents (1/1200 of an octave).

Reference:
    de Cheveigné, A. & Kawahara, H. (2002). YIN, a fundamental frequency estimator for speech and
    music. JASA, 111(4), 1917-1930.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from scipy.signal import resample_poly

from wingbeat_dsp.conditioning import TARGET_RATE_HZ

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

__all__ = ["YinEstimate", "agreement", "cents", "yin"]

DEFAULT_THRESHOLD: Final = 0.1
"""Absolute threshold on the normalised difference, from de Cheveigné & Kawahara (2002)."""


@dataclass(frozen=True, slots=True)
class YinEstimate:
    """A YIN estimate for one frame.

    Attributes:
        f0_hz: Estimated fundamental.
        aperiodicity: Normalised difference at the chosen lag, 0 (periodic) to about 1 (noise).
        periodic: Whether the aperiodicity is below the threshold.
    """

    f0_hz: float
    aperiodicity: float
    periodic: bool


def _normalised_difference(x: NDArray[np.float64], max_lag: int) -> NDArray[np.float64]:
    window = x.size - max_lag
    d = np.empty(max_lag + 1)
    head = x[:window]
    for tau in range(max_lag + 1):
        diff = head - x[tau : tau + window]
        d[tau] = float(np.dot(diff, diff))
    normalised = np.ones_like(d)
    running = np.cumsum(d[1:])
    lags = np.arange(1, max_lag + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        normalised[1:] = np.where(running > 0, d[1:] * lags / running, 1.0)
    return normalised


def yin(  # noqa: PLR0913 - the paper's parameters, all with defaults
    frame: ArrayLike,
    rate_hz: int = TARGET_RATE_HZ,
    *,
    f0_min_hz: float = 250.0,
    f0_max_hz: float = 1_250.0,
    threshold: float = DEFAULT_THRESHOLD,
    upsample: int = 4,
) -> YinEstimate:
    """Estimate the fundamental of one frame.

    Raises:
        ValueError: If the frame is too short for two periods of ``f0_min_hz`` or the
            parameters are invalid.
    """
    signal = np.asarray(frame, dtype=np.float64)
    if not 0 < f0_min_hz < f0_max_hz or upsample < 1 or not 0 < threshold < 1:
        msg = "need 0 < f0_min_hz < f0_max_hz, upsample >= 1 and 0 < threshold < 1"
        raise ValueError(msg)
    x = resample_poly(signal, upsample, 1) if upsample > 1 else signal
    fs = rate_hz * upsample
    min_lag = max(2, math.floor(fs / f0_max_hz))
    max_lag = math.ceil(fs / f0_min_hz)
    if x.size < 2 * max_lag:
        msg = f"frame of {signal.size} samples is too short for {f0_min_hz} Hz"
        raise ValueError(msg)
    d = _normalised_difference(np.asarray(x, dtype=np.float64), max_lag)
    candidates = np.flatnonzero(d[min_lag : max_lag + 1] < threshold)
    if candidates.size:
        tau = int(candidates[0]) + min_lag
        while tau + 1 <= max_lag and d[tau + 1] < d[tau]:
            tau += 1
    else:
        tau = int(np.argmin(d[min_lag : max_lag + 1])) + min_lag
    offset = 0.0
    if min_lag < tau < max_lag:
        a, b, c = d[tau - 1], d[tau], d[tau + 1]
        denominator = a - 2 * b + c
        if denominator > 0:
            offset = float(np.clip(0.5 * (a - c) / denominator, -0.5, 0.5))
    aperiodicity = float(d[tau])
    return YinEstimate(
        f0_hz=fs / (tau + offset), aperiodicity=aperiodicity, periodic=aperiodicity < threshold
    )


def cents(f_a_hz: float, f_b_hz: float) -> float:
    """Signed interval from ``f_b`` to ``f_a`` in cents (1,200 per octave)."""
    return 1_200.0 * math.log2(f_a_hz / f_b_hz)


def agreement(f_a_hz: float, f_b_hz: float, *, tolerance_cents: float = 20.0) -> float:
    """Agreement of two estimates, from 1 (equal) falling linearly to 0 at ``tolerance_cents``.

    20 cents is about 1.2 %, or 6 Hz at 550 Hz. Missing or non-positive estimates score 0.
    """
    if not (f_a_hz > 0 and f_b_hz > 0) or tolerance_cents <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(cents(f_a_hz, f_b_hz)) / tolerance_cents)
