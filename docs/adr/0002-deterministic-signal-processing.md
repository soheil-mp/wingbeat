# 0002. Deterministic, explainable signal processing; no machine learning

- Status: Accepted
- Date: 2026-11-02

## Context and problem statement

Most published acoustic mosquito work uses learned classifiers. Wingbeat aims to be a
data-engineering and operations showcase that anyone can audit, reproduce bit for bit, and run on
a low-power edge device. How should the platform turn audio into detections and species
candidates?

## Decision drivers

- Explainability: every attribution must say *why* (which band, which rule, which evidence).
- Reproducibility: the same input and configuration give the same output on every platform.
- Edge budget: it must run in real time on a Raspberry Pi class CPU with headroom.
- Scientific traceability: parameters come from cited literature, not from fitting.
- Scope: the product contains no machine-learning components at all.

## Considered options

1. Classical DSP estimators plus a literature-parameterised rule engine.
2. A learned classifier trained on public recordings.
3. A hybrid (DSP features into a learned classifier).

## Decision outcome

Chosen option 1. The pipeline is band-pass filtering → noise-floor tracking → harmonic
estimators (harmonic sum or product spectrum, YIN cross-check) → event segmentation with
hysteresis → temperature normalisation (ADR-0009) → rule-based candidate attribution.
All parameters live in a versioned reference table with a citation for every value.

### Consequences

- Good: fully explainable. Each event carries an explanation trace and can be checked by hand.
- Good: deterministic and cheap. Property-based tests can state exact tolerances.
- Good: no training data, model registry or GPU anywhere in the stack.
- Bad: lower species resolution than a well-trained classifier where bands overlap. We accept
  this and report ranked **candidate sets** with an `ambiguous` flag instead of a guess.
- Neutral: words matter in code and docs. We use *estimator*, *rule engine* and *attribution*.

### Confirmation

A dependency allow-list check in CI rejects ML libraries. The verification report (M17) gives
detection characteristics against SNR for planted synthetic events.
