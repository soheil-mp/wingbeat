import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from scipy.signal import sosfreqz

from wingbeat_dsp.filters import (
    StreamingFilter,
    apply,
    bandpass_sos,
    cascade,
    hum_notch_sos,
)

RATE = 8_000


def gain_db(sos: np.ndarray, freq_hz: float) -> float:
    _, response = sosfreqz(sos, worN=[freq_hz], fs=RATE)
    return float(20 * np.log10(np.abs(response[0])))


class TestBandpass:
    @pytest.mark.parametrize("freq_hz", [400.0, 550.0, 700.0, 1_100.0, 1_650.0])
    def test_passes_wingbeat_fundamentals_and_harmonics(self, freq_hz: float) -> None:
        assert abs(gain_db(bandpass_sos(), freq_hz)) < 0.5

    @pytest.mark.parametrize(
        ("freq_hz", "below_db"), [(50.0, -40.0), (100.0, -25.0), (3_800.0, -20.0)]
    )
    def test_rejects_out_of_band(self, freq_hz: float, below_db: float) -> None:
        assert gain_db(bandpass_sos(), freq_hz) < below_db

    def test_edges_are_at_minus_3_db(self) -> None:
        assert gain_db(bandpass_sos(), 250.0) == pytest.approx(-3.01, abs=0.1)
        assert gain_db(bandpass_sos(), 2_500.0) == pytest.approx(-3.01, abs=0.1)

    def test_rejects_bands_outside_nyquist(self) -> None:
        with pytest.raises(ValueError, match="Nyquist"):
            bandpass_sos(high_hz=4_000.0)


class TestHumNotch:
    @pytest.mark.parametrize("mains_hz", [50.0, 60.0])
    def test_notches_the_mains_harmonics(self, mains_hz: float) -> None:
        sos = hum_notch_sos(mains_hz)
        for k in range(1, 6):
            assert gain_db(sos, k * mains_hz) < -40

    @pytest.mark.parametrize("freq_hz", [342.0, 450.0, 550.0, 600.0, 737.0])
    def test_leaves_wingbeat_fundamentals_alone(self, freq_hz: float) -> None:
        # 550 and 600 Hz are harmonics of 50 Hz but lie above the notched range.
        assert abs(gain_db(hum_notch_sos(50.0), freq_hz)) < 0.2
        assert abs(gain_db(hum_notch_sos(60.0), freq_hz)) < 0.2

    @pytest.mark.parametrize(
        "kwargs", [{"harmonics": 0}, {"quality": 0.0}, {"mains_hz": 50.0, "harmonics": 80}]
    )
    def test_rejects_bad_parameters(self, kwargs: dict[str, float]) -> None:
        with pytest.raises(ValueError):  # noqa: PT011 - each case has its own message
            hum_notch_sos(**kwargs)  # type: ignore[arg-type]


def test_chain_removes_hum_and_keeps_the_tone() -> None:
    t = np.arange(RATE * 2) / RATE
    wing = 0.1 * np.sin(2 * np.pi * 550 * t)
    hum = 0.5 * np.sin(2 * np.pi * 50 * t) + 0.2 * np.sin(2 * np.pi * 150 * t)
    out = apply(cascade(bandpass_sos(), hum_notch_sos(50.0)), wing + hum)[RATE:]
    assert float(np.sqrt(np.mean(out**2))) == pytest.approx(0.1 / np.sqrt(2), rel=0.03)
    spectrum = np.abs(np.fft.rfft(out))
    freqs = np.fft.rfftfreq(out.size, 1 / RATE)
    assert spectrum[freqs == 50.0][0] < 1e-3 * spectrum[freqs == 550.0][0]


@settings(max_examples=30)
@given(st.lists(st.integers(0, 900), min_size=1, max_size=10))
def test_streaming_matches_batch_for_any_chunking(sizes: list[int]) -> None:
    sos = cascade(bandpass_sos(), hum_notch_sos(60.0))
    signal = np.random.default_rng(3).normal(0, 1, sum(sizes))
    stream = StreamingFilter(sos)
    parts = [stream.process(c) for c in np.split(signal, np.cumsum(sizes)[:-1])]
    np.testing.assert_allclose(np.concatenate(parts), apply(sos, signal), atol=1e-10)


def test_reset_returns_to_rest() -> None:
    stream = StreamingFilter(bandpass_sos())
    stream.process(np.ones(500))
    stream.reset()
    impulse = np.zeros(64)
    impulse[0] = 1.0
    np.testing.assert_allclose(stream.process(impulse), apply(bandpass_sos(), impulse))
