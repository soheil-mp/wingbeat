import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wingbeat_dsp.harmonic import (
    HarmonicConfig,
    Method,
    _octave_guard,
    estimate_f0,
    harmonic_power_fraction,
)
from wingbeat_dsp.spectral import welch_psd

RATE = 8_000
T = np.arange(RATE * 2) / RATE


def stack(f0: float, amplitudes: list[float], noise: float = 0.01, seed: int = 0) -> np.ndarray:
    signal = sum(
        a * np.sin(2 * np.pi * (k + 1) * f0 * T + 0.3 * k) for k, a in enumerate(amplitudes)
    )
    return np.asarray(signal) + np.random.default_rng(seed).normal(0, noise, T.size)


CASES = {
    "falling harmonics": (550.0, [1.0, 0.6, 0.4, 0.3]),
    "strong second harmonic": (550.0, [0.3, 1.0, 0.5, 0.3]),
    "missing fundamental": (550.0, [0.0, 1.0, 0.7, 0.5]),
    "high fundamental": (1_100.0, [1.0, 0.5, 0.3]),
    "lowest literature f0": (342.6, [1.0, 0.5, 0.3, 0.2]),
    "highest female f0": (737.4, [1.0, 0.4, 0.2]),
}


@pytest.mark.parametrize("method", list(Method))
@pytest.mark.parametrize("case", list(CASES))
def test_estimates_are_within_half_a_hertz(case: str, method: Method) -> None:
    f0, amplitudes = CASES[case]
    estimate = estimate_f0(welch_psd(stack(f0, amplitudes)), method)
    assert estimate.f0_hz == pytest.approx(f0, abs=0.5)
    assert estimate.method is method
    assert estimate.harmonic_power_fraction > 0.95


def test_guard_halves_an_octave_too_high_candidate() -> None:
    spectrum = welch_psd(stack(550.0, [0.4, 1.0, 0.6, 0.4]))
    f0, corrected = _octave_guard(spectrum, 1_100.0, HarmonicConfig())
    assert corrected
    assert f0 == pytest.approx(550.0)


def test_guard_keeps_a_genuine_high_fundamental() -> None:
    spectrum = welch_psd(stack(1_100.0, [1.0, 0.5, 0.3]))
    assert _octave_guard(spectrum, 1_100.0, HarmonicConfig()) == (1_100.0, False)


def test_guard_doubles_an_octave_too_low_candidate() -> None:
    spectrum = welch_psd(stack(701.0, [1.0, 1.0], noise=0.2))
    f0, corrected = _octave_guard(spectrum, 350.5, HarmonicConfig())
    assert corrected
    assert f0 == pytest.approx(701.0)


def test_noise_has_a_low_harmonic_power_fraction() -> None:
    spectrum = welch_psd(np.random.default_rng(5).normal(0, 0.1, T.size))
    assert estimate_f0(spectrum).harmonic_power_fraction < 0.2
    assert harmonic_power_fraction(welch_psd(np.zeros(T.size)), 550.0) == 0.0


def test_rejects_an_empty_search_range() -> None:
    with pytest.raises(ValueError, match="f0_min_hz"):
        estimate_f0(
            welch_psd(stack(550.0, [1.0])), config=HarmonicConfig(f0_min_hz=600, f0_max_hz=500)
        )


@settings(max_examples=25, deadline=None)
@given(
    f0=st.floats(300.0, 800.0),
    amplitudes=st.lists(st.floats(0.2, 1.0), min_size=2, max_size=4),
    seed=st.integers(0, 2**32 - 1),
)
def test_f0_error_is_under_2_hz_at_10_db_snr(f0: float, amplitudes: list[float], seed: int) -> None:
    signal_power = sum(a**2 / 2 for a in amplitudes)
    noise_sd = float(np.sqrt(signal_power / 10))  # SNR = 10 dB
    spectrum = welch_psd(stack(f0, amplitudes, noise=noise_sd, seed=seed))
    assert estimate_f0(spectrum).f0_hz == pytest.approx(f0, abs=2.0)


@settings(max_examples=15, deadline=None)
@given(gain=st.floats(1e-3, 1e3), f0=st.floats(320.0, 760.0))
def test_estimates_do_not_depend_on_gain(gain: float, f0: float) -> None:
    signal = stack(f0, [1.0, 0.5, 0.3])
    a = estimate_f0(welch_psd(signal)).f0_hz
    b = estimate_f0(welch_psd(gain * signal)).f0_hz
    assert b == pytest.approx(a, abs=1e-6)
