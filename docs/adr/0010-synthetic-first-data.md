# 0010. Synthetic-first data with tightly capped real sources

- Status: Accepted
- Date: 2026-11-02

## Context and problem statement

Public mosquito audio archives are large (HumBugDB is 4.1 GB), development disk space is limited,
and real field audio carries privacy risk. We still need realistic, high-volume streams to
exercise a real-time platform.

## Decision outcome

- The **primary stream is synthetic**: a physically grounded sensor fleet simulator driven by
  literature frequencies, real weather, regional species lists and diel activity curves, with
  fault injection. It is deterministic per seed, scales to thousands of virtual sensors, and
  stores nothing.
- **Real recordings** come in only through capped, selective ingestion: HTTP range requests pull
  single entries out of remote zip archives, with a 25 MB cap, an allow-listed `sound_type`, a
  content hash and a licence ledger.
- **Reference data** (weather, species presence, regions) is small, refreshed on a schedule, and
  cached with ETags.

### Consequences

- Good: zero-storage load tests, reproducible end-to-end tests, and no personal data.
- Bad: simulated data can flatter the detector. The verification report states where planted
  signals differ from real ones, and real reference clips are replayed in every e2e run.

### Confirmation

An asset check enforces the per-source caps, and the CI e2e job runs on a fresh runner with
under 1 GB of downloaded data.
