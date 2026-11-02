# Wingbeat

Wingbeat is an open platform for monitoring mosquitoes by their sound, in real time. A
microphone in a trap hears the wingbeat tone. A deterministic signal-processing pipeline on the
edge device turns it into a detection with a temperature-normalised frequency and a ranked set of
candidate species. A streaming data platform carries every detection to live dashboards, a
lakehouse, data-quality gates and alerts.

!!! info "Status"
    Planning is complete and the workspace tooling is in place. Implementation proceeds milestone
    by milestone; the [roadmap](https://github.com/soheil-mp/wingbeat/blob/main/ROADMAP.md)
    tracks every item with an estimate.

## Start here

- **[Architecture](architecture.md):** containers, data flow, delivery guarantees and naming.
- **[The acoustics of mosquito flight](research/science.md):** the literature behind every
  number in the reference table, including why temperature normalisation matters.
- **[Data sources and licences](research/data-sources.md):** what is ingested, how much, and
  under which licence.
- **[Technology landscape](research/technology-landscape.md):** the stack, the versions checked
  and the alternatives rejected.
- **[Decisions](adr/README.md):** the architecture decision records.

## Principles

- **Explainable by construction:** classical estimators and a cited rule table, no machine
  learning anywhere.
- **Honest about uncertainty:** candidate sets with an explicit `ambiguous` flag.
- **Private by design:** raw audio never leaves the device.
- **Frugal by design:** the whole platform runs on one laptop with at most 2 GB of data.

## Data attribution

Mosquito reference recordings: HumBugDB (Kiskin et al. 2021), CC BY 4.0. Species presence:
GBIF.org and VectorNet (ECDC/EFSA), CC BY 4.0. Weather data by Open-Meteo.com, CC BY 4.0.
Administrative boundaries: © EuroGeographics, source: European Commission – Eurostat/GISCO.
