"""Framing and conditioning: the first stage of the pipeline (ROADMAP M2.2).

Mosquito wingbeat fundamentals lie between about 340 and 740 Hz (Kim et al. 2021), and the
fundamental plus its first harmonics fit in 250-2,500 Hz, so audio is resampled to **8 kHz**
(Nyquist 4 kHz) before anything else. DC is removed, and the signal is cut into overlapping
windowed frames for spectral estimation.

Every step has a pure batch function and a stateful streaming class. The streaming classes give
exactly the same output as the batch functions however the input is split into chunks, which
the tests check.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Final

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import get_window, lfilter, resample_poly

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "DEFAULT_FRAME_LENGTH",
    "DEFAULT_HOP_LENGTH",
    "TARGET_RATE_HZ",
    "DcBlocker",
    "Framer",
    "frame",
    "remove_dc",
    "resample",
]

TARGET_RATE_HZ: Final = 8_000
"""Sample rate of every signal after conditioning."""

DEFAULT_FRAME_LENGTH: Final = 1_024
"""Samples per frame: 128 ms at 8 kHz, a 7.8 Hz bin before peak interpolation."""

DEFAULT_HOP_LENGTH: Final = 512
"""Samples between frame starts: 50 % overlap."""


def _mono(samples: ArrayLike) -> NDArray[np.float64]:
    signal = np.asarray(samples, dtype=np.float64)
    if signal.ndim != 1:
        msg = f"expected a one-dimensional signal, got shape {signal.shape}"
        raise ValueError(msg)
    return signal


def resample(
    samples: ArrayLike, rate_hz: int, target_hz: int = TARGET_RATE_HZ
) -> NDArray[np.float64]:
    """Resample with a polyphase FIR filter (up and down factors reduced by their GCD).

    Raises:
        ValueError: If a rate is not positive or the signal is not one-dimensional.
    """
    signal = _mono(samples)
    if rate_hz <= 0 or target_hz <= 0:
        msg = f"sample rates must be positive, got {rate_hz} and {target_hz}"
        raise ValueError(msg)
    if rate_hz == target_hz:
        return signal
    common = math.gcd(rate_hz, target_hz)
    return np.asarray(
        resample_poly(signal, target_hz // common, rate_hz // common), dtype=np.float64
    )


def remove_dc(samples: ArrayLike) -> NDArray[np.float64]:
    """Subtract the mean (batch DC removal)."""
    signal = _mono(samples)
    return signal - signal.mean() if signal.size else signal


def frame(
    samples: ArrayLike,
    *,
    frame_length: int = DEFAULT_FRAME_LENGTH,
    hop_length: int = DEFAULT_HOP_LENGTH,
    window: str = "hann",
) -> NDArray[np.float64]:
    """Cut a signal into windowed frames, shape ``(n_frames, frame_length)``.

    Trailing samples that do not fill a frame are dropped; a signal shorter than one frame gives
    zero frames.

    Raises:
        ValueError: If the lengths are not positive or the hop exceeds the frame length.
    """
    signal = _mono(samples)
    _check_lengths(frame_length, hop_length)
    taper = np.asarray(get_window(window, frame_length, fftbins=True), dtype=np.float64)
    if signal.size < frame_length:
        return np.empty((0, frame_length))
    return sliding_window_view(signal, frame_length)[::hop_length] * taper


def _check_lengths(frame_length: int, hop_length: int) -> None:
    if frame_length < 2 or not 0 < hop_length <= frame_length:  # noqa: PLR2004
        msg = (
            "need frame_length >= 2 and 0 < hop_length <= frame_length, "
            f"got {frame_length} and {hop_length}"
        )
        raise ValueError(msg)


class DcBlocker:
    """Streaming DC removal with the one-pole high-pass ``y[n] = x[n] - x[n-1] + r * y[n-1]``.

    The pole radius ``r`` sets the corner frequency, about ``(1 - r) * fs / (2 * pi)``: 0.995 at
    8 kHz gives about 6 Hz, far below the 250 Hz band edge. Unlike :func:`remove_dc`, it needs
    no look-ahead, so it runs on the edge device chunk by chunk.
    """

    def __init__(self, pole: float = 0.995) -> None:
        """Create a blocker with zero initial state.

        Raises:
            ValueError: If the pole is not in (0, 1).
        """
        if not 0 < pole < 1:
            msg = f"pole must be in (0, 1), got {pole}"
            raise ValueError(msg)
        self.pole = pole
        self._x = 0.0
        self._y = 0.0

    def process(self, chunk: ArrayLike) -> NDArray[np.float64]:
        """Filter one chunk, continuing from the previous chunk's state."""
        x = _mono(chunk)
        if x.size == 0:
            return x
        # Initial conditions that continue the recursion across chunks.
        zi = np.array([self.pole * self._y - self._x])
        y, _ = lfilter([1.0, -1.0], [1.0, -self.pole], x, zi=zi)
        self._x, self._y = float(x[-1]), float(y[-1])
        return np.asarray(y, dtype=np.float64)


class Framer:
    """Streaming framing: feed chunks of any size, get the same frames as :func:`frame`."""

    def __init__(
        self,
        *,
        frame_length: int = DEFAULT_FRAME_LENGTH,
        hop_length: int = DEFAULT_HOP_LENGTH,
        window: str = "hann",
    ) -> None:
        """Create a framer with an empty buffer."""
        _check_lengths(frame_length, hop_length)
        self.frame_length = frame_length
        self.hop_length = hop_length
        self._taper = np.asarray(get_window(window, frame_length, fftbins=True), dtype=np.float64)
        self._buffer = np.empty(0)
        self.frames_emitted = 0

    def push(self, chunk: ArrayLike) -> NDArray[np.float64]:
        """Add samples; returns every frame completed by them, shape ``(n, frame_length)``."""
        self._buffer = np.concatenate((self._buffer, _mono(chunk)))
        if self._buffer.size < self.frame_length:
            return np.empty((0, self.frame_length))
        frames = sliding_window_view(self._buffer, self.frame_length)[:: self.hop_length]
        out = frames * self._taper
        self._buffer = self._buffer[len(frames) * self.hop_length :]
        self.frames_emitted += len(frames)
        return out
