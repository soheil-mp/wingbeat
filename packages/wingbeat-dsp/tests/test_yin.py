import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wingbeat_dsp.harmonic import estimate_f0
from wingbeat_dsp.spectral import welch_psd
from wingbeat_dsp.yin import agreement, cents, yin

RATE = 8_000


def stack(
    f0: float, amplitudes: list[float], n: int = 1_024, noise: float = 0.02, seed: int = 0
) -> np.ndarray:
    t = np.arange(n) / RATE
    signal = sum(
        a * np.sin(2 * np.pi * (k + 1) * f0 * t + 0.4 * k) for k, a in enumerate(amplitudes)
    )
    return np.asarray(signal) + np.random.default_rng(seed).normal(0, noise, n)


@pytest.mark.parametrize(
    ("f0", "amplitudes"),
    [
        (342.6, [1.0]),
        (550.0, [1.0, 0.6, 0.4]),
        (550.0, [0.0, 1.0, 0.7, 0.5]),  # missing fundamental: the period is still 1/550 s
        (612.3, [0.3, 1.0, 0.5]),  # strong second harmonic
        (737.4, [1.0, 0.4]),
    ],
)
def test_periodic_frames(f0: float, amplitudes: list[float]) -> None:
    estimate = yin(stack(f0, amplitudes))
    assert estimate.f0_hz == pytest.approx(f0, abs=0.5)
    assert estimate.periodic
    assert estimate.aperiodicity < 0.01


def test_noise_is_aperiodic() -> None:
    estimate = yin(np.random.default_rng(1).normal(0, 1, 1_024))
    assert not estimate.periodic
    assert estimate.aperiodicity > 0.5


def test_upsampling_improves_precision() -> None:
    frame = stack(617.0, [1.0, 0.5])
    coarse = abs(yin(frame, upsample=1).f0_hz - 617.0)
    fine = abs(yin(frame).f0_hz - 617.0)
    assert fine < coarse


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [({"f0_min_hz": 900.0, "f0_max_hz": 800.0}, "f0_min_hz"), ({"threshold": 0.0}, "threshold")],
)
def test_rejects_bad_parameters(kwargs: dict[str, float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        yin(stack(550.0, [1.0]), **kwargs)  # type: ignore[arg-type]


def test_rejects_frames_shorter_than_two_periods() -> None:
    with pytest.raises(ValueError, match="too short"):
        yin(np.zeros(40))


@settings(max_examples=25, deadline=None)
@given(f0=st.floats(300.0, 800.0), seed=st.integers(0, 2**32 - 1))
def test_yin_agrees_with_the_harmonic_estimator(f0: float, seed: int) -> None:
    long_signal = stack(f0, [1.0, 0.5, 0.3], n=RATE, noise=0.05, seed=seed)
    harmonic = estimate_f0(welch_psd(long_signal)).f0_hz
    time_domain = yin(long_signal[:1_024]).f0_hz
    assert agreement(harmonic, time_domain) > 0.8


class TestAgreement:
    def test_cents(self) -> None:
        assert cents(1_100.0, 550.0) == pytest.approx(1_200.0)
        assert cents(550.0, 1_100.0) == pytest.approx(-1_200.0)

    def test_scores(self) -> None:
        assert agreement(550.0, 550.0) == 1.0
        assert agreement(550.0 * 2 ** (10 / 1_200), 550.0) == pytest.approx(0.5)
        assert agreement(1_100.0, 550.0) == 0.0  # an octave apart
        assert agreement(math.nan, 550.0) == 0.0
        assert agreement(550.0, 0.0) == 0.0
        assert agreement(550.0, 551.0, tolerance_cents=0.0) == 0.0
