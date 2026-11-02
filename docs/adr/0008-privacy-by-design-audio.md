# 0008. Privacy by design: raw audio never leaves the device

- Status: Accepted
- Date: 2026-11-02

## Context and problem statement

Acoustic sensors near homes or parks will pick up people. Speech in eco-acoustic recordings is
intelligible up to about 10 m (Cretois et al. 2022). Under the GDPR, recordings of identifiable
voices are personal data. Wingbeat must not collect personal data.

## Decision outcome

1. **On-device processing.** Audio lives in a RAM ring buffer of a few seconds and is never
   written to disk or sent by default.
2. **Features-only uplink.** Only detection events (*f0*, harmonic amplitudes, SNR, duration,
   explanation trace) and coarse band-limited spectral summaries leave the device. Summaries
   are capped at the mosquito band (250–2,500 Hz) and ≤ 4 frames per second, a resolution far
   below what intelligible speech reconstruction needs.
3. **Deterministic speech guard.** Before feature extraction, frames whose envelope shows
   syllabic-rate modulation (about 2–8 Hz) with voiced pitch in the human range are dropped and
   counted, never stored. Only the count of guarded frames is reported as telemetry.
4. **Debug clip capture** is off by default. When enabled it is time-limited, stays local, and
   still passes through the guard.
5. **Reference recordings** are restricted to lab-culture mosquito clips (see
   `docs/research/data-sources.md`).

### Consequences

- Good: no personal data in Kafka, the lake or backups, by construction.
- Bad: raw audio can't be re-analysed later. Reprocessing works from features or re-runs at the
  edge. We accept this.

### Confirmation

A unit test plays synthetic speech-like signals (voiced harmonic stacks with syllabic AM) through
the guard and expects zero uplinked frames. An integration test checks that no topic schema has a
raw-sample field. The M16 verification report includes guard false-positive and false-negative
rates on synthetic signals.
