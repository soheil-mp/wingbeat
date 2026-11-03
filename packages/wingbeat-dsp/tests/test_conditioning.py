import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from wingbeat_dsp.conditioning import (
    TARGET_RATE_HZ,
    DcBlocker,
    Framer,
    frame,
    remove_dc,
    resample,
)


def tone(freq_hz: float, rate_hz: int, seconds: float = 1.0, amplitude: float = 0.3) -> np.ndarray:
    t = np.arange(round(rate_hz * seconds)) / rate_hz
    return amplitude * np.sin(2 * np.pi * freq_hz * t)


def peak_hz(signal: np.ndarray, rate_hz: int) -> float:
    spectrum = np.abs(np.fft.rfft(signal * np.hanning(signal.size)))
    return float(np.fft.rfftfreq(signal.size, 1 / rate_hz)[np.argmax(spectrum)])


@pytest.mark.parametrize("rate_hz", [16_000, 22_050, 44_100, 48_000])
def test_resampling_keeps_a_wingbeat_tone(rate_hz: int) -> None:
    out = resample(tone(550.0, rate_hz), rate_hz)
    assert out.size == pytest.approx(TARGET_RATE_HZ, abs=1)
    assert peak_hz(out, TARGET_RATE_HZ) == pytest.approx(550.0, abs=1.0)
    edge = TARGET_RATE_HZ // 20
    rms = float(np.sqrt(np.mean(out[edge:-edge] ** 2)))
    assert rms == pytest.approx(0.3 / np.sqrt(2), rel=0.01)


def test_resampling_removes_content_above_4_khz() -> None:
    out = resample(tone(6_000.0, 48_000), 48_000)
    assert float(np.sqrt(np.mean(out[500:-500] ** 2))) < 0.003


def test_resampling_at_the_target_rate_is_a_no_op() -> None:
    signal = tone(500.0, TARGET_RATE_HZ)
    np.testing.assert_array_equal(resample(signal, TARGET_RATE_HZ), signal)
    with pytest.raises(ValueError, match="positive"):
        resample(signal, 0)
    with pytest.raises(ValueError, match="one-dimensional"):
        resample(np.zeros((2, 2)), 8_000)


def test_remove_dc() -> None:
    out = remove_dc(tone(500.0, TARGET_RATE_HZ) + 0.2)
    assert abs(float(out.mean())) < 1e-12
    assert remove_dc(np.zeros(0)).size == 0


def test_dc_blocker_removes_an_offset_and_keeps_the_band() -> None:
    signal = tone(500.0, TARGET_RATE_HZ, seconds=3.0) + 0.2
    out = DcBlocker().process(signal)
    tail = out[TARGET_RATE_HZ:]
    assert abs(float(tail.mean())) < 1e-3
    assert float(np.sqrt(np.mean(tail**2))) == pytest.approx(0.3 / np.sqrt(2), rel=0.01)


@settings(max_examples=30)
@given(st.lists(st.integers(0, 700), min_size=1, max_size=12))
def test_dc_blocker_is_chunk_invariant(sizes: list[int]) -> None:
    signal = np.random.default_rng(1).normal(0.1, 0.05, sum(sizes))
    whole = DcBlocker().process(signal)
    blocker = DcBlocker()
    parts = np.concatenate([blocker.process(c) for c in np.split(signal, np.cumsum(sizes)[:-1])])
    np.testing.assert_allclose(parts, whole, atol=1e-12)


def test_dc_blocker_rejects_bad_poles() -> None:
    with pytest.raises(ValueError, match="pole"):
        DcBlocker(1.0)


def test_frame_shapes_and_window() -> None:
    frames = frame(np.ones(4_096), frame_length=1_024, hop_length=512)
    assert frames.shape == (7, 1_024)
    np.testing.assert_allclose(frames[0], np.hanning(1_025)[:-1], atol=1e-12)
    assert frame(np.ones(100)).shape == (0, 1_024)


@pytest.mark.parametrize(("length", "hop"), [(1, 1), (1_024, 0), (512, 1_024)])
def test_frame_rejects_bad_lengths(length: int, hop: int) -> None:
    with pytest.raises(ValueError, match="frame_length"):
        frame(np.ones(10), frame_length=length, hop_length=hop)


@settings(max_examples=30)
@given(
    sizes=st.lists(st.integers(0, 3_000), min_size=1, max_size=10),
    hop=st.sampled_from([256, 512, 1_024]),
)
def test_framer_is_chunk_invariant(sizes: list[int], hop: int) -> None:
    signal = np.random.default_rng(2).normal(0, 1, sum(sizes))
    framer = Framer(frame_length=1_024, hop_length=hop)
    parts = [framer.push(c) for c in np.split(signal, np.cumsum(sizes)[:-1])]
    streamed = np.concatenate(parts) if parts else np.empty((0, 1_024))
    batch = frame(signal, frame_length=1_024, hop_length=hop)
    np.testing.assert_allclose(streamed, batch)
    assert framer.frames_emitted == len(batch)
