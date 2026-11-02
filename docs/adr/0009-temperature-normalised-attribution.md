# 0009. Temperature-normalised, candidate-set species attribution

- Status: Accepted (validate in M1/M2)
- Date: 2026-11-02

## Context and problem statement

Wingbeat frequency rises with air temperature, by about 9.6 Hz/°C near 500 Hz (Saha et al.
2024; Villarreal et al. 2017). A 15 °C daily swing shifts a tone more than the gap between some
species. Bands also overlap: 26 of 29 species in Kim et al. (2021) overlapped with at least one
other.

## Decision outcome

1. **Normalise** every detection's *f0* to *T_ref* = 20 °C with the Saha et al. (2024) Eq. 3
   correction. Species-level slopes from the reference table override it where a source exists.
   Temperature comes from the sensor's own thermometer when present, otherwise from the nearest
   hourly weather value (Open-Meteo), and the source is recorded in the event (`temp_source`).
2. **Attribute to a candidate set**, not a single label. For each reference row (species × sex)
   compute the distance in standard deviations from the normalised *f0* and the harmonic
   evidence. Filter by regional presence (VectorNet status, GBIF facets) and by the diel activity
   window. Rank the candidates and set `ambiguous = true` when the top two are within a margin.
3. **Explain** every decision with a trace of the rules that fired, the evidence values and the
   reference rows (with citations) used.

### Consequences

- Good: honest about uncertainty, fully auditable, and it uses open data as context.
- Bad: needs a reliable temperature for each event. Missing temperatures are flagged, and those
  events are attributed with widened bands.

### Confirmation

Property-based tests: a planted tone at known species, sex and temperature attributes to a
candidate set containing the planted species for every temperature from 10 °C to 35 °C. The
"raw vs normalised *f0*" Grafana panel shows the bands collapse after normalisation on simulated
diurnal temperature cycles.
