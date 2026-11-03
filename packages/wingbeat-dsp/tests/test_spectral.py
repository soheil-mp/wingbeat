import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wingbeat_dsp.spectral import (
    Spectrum,
    dominant_peak,
    interpolate_peak,
    spectral_flatness,
    welch_psd,
)

RATE = 8_000
T = np.arange(RATE * 2) / RATE


def tone(freq_hz: float, amplitude: float = 0.3) -> np.ndarray:
    return amplitude * np.sin(2 * np.pi * freq_hz * T)


def test_welch_preserves_power() -> None:
    noise = np.random.default_rng(0).normal(0, 0.2, RATE * 10)
    spectrum = welch_psd(noise)
    assert float(spectrum.psd.sum() * spectrum.bin_width_hz) == pytest.approx(0.04, rel=0.03)
    assert spectrum.bin_width_hz == pytest.approx(RATE / 1_024)


def test_welch_rejects_short_or_multichannel_input() -> None:
    with pytest.raises(ValueError, match="at least 1024"):
        welch_psd(np.zeros(100))
    with pytest.raises(ValueError, match="1-D"):
        welch_psd(np.zeros((2, 2_000)))


@settings(max_examples=40, deadline=None)
@given(freq=st.floats(300.0, 2_400.0), seed=st.integers(0, 2**32 - 1))
def test_interpolated_peak_is_well_within_a_hertz(freq: float, seed: int) -> None:
    noisy = tone(freq) + np.random.default_rng(seed).normal(0, 0.01, T.size)
    peak = dominant_peak(welch_psd(noisy))
    assert abs(peak.frequency_hz - freq) < 0.5


def test_peak_search_is_limited_to_the_band() -> None:
    signal = tone(3_000.0, amplitude=1.0) + tone(600.0, amplitude=0.1)
    assert dominant_peak(welch_psd(signal)).frequency_hz == pytest.approx(600.0, abs=0.5)
    with pytest.raises(ValueError, match="no bins"):
        dominant_peak(welch_psd(signal), low_hz=5_000.0, high_hz=6_000.0)


def test_interpolation_edge_cases() -> None:
    values = np.array([0.0, 10.0, 5.0])
    assert interpolate_peak(values, 0) == (0.0, 0.0)
    assert interpolate_peak(np.array([1.0, 1.0, 1.0]), 1) == (0.0, 1.0)  # flat: no peak
    offset, level = interpolate_peak(np.array([5.0, 10.0, 5.0]), 1)
    assert (offset, level) == (0.0, 10.0)
    # The peak leans towards the higher neighbour.
    assert 0 < interpolate_peak(values, 1)[0] <= 0.5
    assert -0.5 <= interpolate_peak(np.array([9.0, 10.0, 0.0]), 1)[0] < 0


def test_flatness_separates_tones_from_noise() -> None:
    noise = np.random.default_rng(1).normal(0, 1, RATE * 10)
    assert spectral_flatness(welch_psd(noise)) > 0.95
    assert spectral_flatness(welch_psd(tone(550.0))) < 1e-3
    assert math.isnan(spectral_flatness(welch_psd(np.zeros(RATE))))


def test_flatness_is_independent_of_gain() -> None:
    noise = np.random.default_rng(2).normal(0, 1, T.size) + tone(700.0)
    assert spectral_flatness(welch_psd(5 * noise)) == pytest.approx(
        spectral_flatness(welch_psd(noise))
    )


def test_flatness_rejects_an_empty_band() -> None:
    spectrum = Spectrum(np.array([0.0, 1.0]), np.array([1.0, 1.0]))
    with pytest.raises(ValueError, match="no bins"):
        spectral_flatness(spectrum, low_hz=10.0, high_hz=20.0)
