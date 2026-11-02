# Data sources, licences and storage budget

> Status: research note for roadmap milestones M3 and M9. Checked on 2 November 2026; every
> number in this file was read from the source on that day.

Wingbeat is built to run on a laptop with little free disk space. Each source has a hard size cap
enforced in code (an asset check fails the run when the cap is exceeded), and the platform keeps
derived features rather than raw audio.

## Overview

| # | Source | What we take | Licence | Access | Upstream size | Our cap |
| :-- | :-- | :-- | :-- | :-- | --: | --: |
| 1 | Wingbeat simulator (this repo) | Synthetic audio frames and detection events for a virtual sensor fleet | MIT (ours) | Generated live | unbounded | 0 B on disk; Kafka keeps 24 h |
| 2 | HumBugDB v0.0.1 (Zenodo) | ≤ 40 short lab mosquito clips, via HTTP range requests | CC BY 4.0 | HTTPS, no key | 4.1 GB | 25 MB |
| 3 | GBIF occurrence API | Species counts for the family Culicidae per country (facets only) | per record: CC0 / CC BY / CC BY-NC | HTTPS, no key | 20,159 NL records | < 1 MB |
| 4 | VectorNet distribution status 2026 (via GBIF) | Regional (NUTS3) presence or absence status of mosquito species | CC BY 4.0 | Darwin Core Archive, no key | a few MB | 10 MB |
| 5 | Open-Meteo forecast and historical APIs | Hourly temperature, humidity, wind, precipitation per sensor site | CC BY 4.0, free for non-commercial use | HTTPS, no key | n/a | < 50 MB/year |
| 6 | Eurostat GISCO NUTS 2024 boundaries | NUTS3 polygons at 1:60M for site → region lookup | © EuroGeographics; terms to confirm | HTTPS, no key | ~ few MB | 10 MB |
| 7 | Own recordings (future): AudioMoth files, own microphone | Features only; raw audio stays on the device | ours | local | n/a | features only |

Total budget for downloaded and derived data: **≤ 2 GB**, plus container images (~4 GB for the
full stack). Default retention is 24 h for Kafka topics and 30 days for raw rows in ClickHouse.
The lake is compacted daily.

## 1. Simulator (primary source)

The simulator is the main data source because it costs no storage, has no licence or privacy
risk, and lets tests plant known events. It is physically grounded: species mix from source 3,
temperature and wind from source 5, frequencies from `docs/research/science.md`. Planted events
are written to a separate manifest so end-to-end tests can check that the platform found them.

## 2. HumBugDB (real reference recordings)

- **Record:** "HumBugDB: a large-scale acoustic mosquito dataset", Zenodo, version 0.0.1,
  doi:10.5281/zenodo.4904800. **Licence:** CC BY 4.0. Attribution: Kiskin et al. 2021.
- **Files:** four zip parts (1.0 GB, 1.1 GB, 1.3 GB, 592.8 MB) and a 1.5 MB metadata CSV,
  `neurips_2021_zenodo_0_0_1.csv`.
- **Metadata on 2026-11-02:** 9,295 rows: 6,795 `mosquito`, 1,900 `background`, 600 `audio`.
  Sample rates are 44.1 kHz (6,102) and 8 kHz (3,193). Countries: Tanzania, Thailand, UK, Kenya,
  USA. Location types: `cup` (6,061), `culture` (2,071), `field` (1,163). Median clip length is
  5.1 s. Columns: `id, length, name, sample_rate, record_datetime, sound_type, species, gender,
  fed, plurality, age, method, mic_type, device_type, country, district, province, place,
  location_type`. None of them identifies a person.
- **Range requests:** Zenodo answered a `Range:` request on the 592.8 MB part with `206 Partial
  Content`, and the zip end-of-central-directory record was in the last bytes. The ingester can
  therefore read the zip directory remotely and fetch single entries without downloading the
  archive. That brings a 4.1 GB source down to a few MB.
- **Selection policy (privacy first):** only `sound_type = mosquito` and `location_type IN
  (culture, cup)`. `background` and `audio` clips are never fetched because they may contain
  human speech, and `field` clips are excluded for the same reason. Clips are stratified by
  species and capped at 40 clips and 25 MB.
- **Use:** a real-signal replay source for the edge agent and a cross-check that the
  estimators' *f0* falls inside the literature band for the labelled species. Wingbeat
  parameters come from the literature and are **never fitted to these clips**.

## 3. GBIF species facets

- Endpoint: `https://api.gbif.org/v1/occurrence/search?familyKey=3346&country=NL&limit=0&facet=speciesKey`.
  Family key 3346 is Culicidae. No key is needed.
- Only facet **counts** are stored (species key, scientific name, count), never occurrence
  records. This keeps personal fields such as `recordedBy` out of the platform by construction.
- On 2026-11-02 the top Dutch species were *Aedes vexans* (1,411), *Culiseta annulata* (1,166),
  *Culex pipiens* (927), *Anopheles messeae* (849), *Ae. albopictus* (245),
  *An. maculipennis* (214), *An. claviger* (173), *Culiseta morsitans* (160), *An. daciae* (144),
  *Coquillettidia richiardii* (135), *An. plumbeus* (123), *Culex territans* (122) and
  *Ae. japonicus* (119).
- Counts reflect sampling effort, not abundance. Wingbeat uses them only as a presence list.
- Attribution: `GBIF.org (accessed YYYY-MM-DD) GBIF Occurrence Search`. A citable download DOI
  needs a GBIF account, so it's an optional extra (`GBIF_USERNAME` / `GBIF_PASSWORD` would go in
  `.env.example`).

## 4. VectorNet distribution status 2026

- GBIF dataset `43411a7a-1503-4391-9791-e33801752053`, "VectorDistributionStatus_2026",
  doi:10.15468/7e3bwm, **CC BY 4.0**, published 29 May 2026 by VectorNet (ECDC/EFSA).
- Content: expert-assessed establishment status of arthropod vectors at NUTS3 (or NUTS2) level
  for Austria, Belgium, Denmark, Germany, the Netherlands, England, Scotland and Wales, with
  GAUL units outside the EU/EEA. It uses NUTS 2024. The data holds 3,972 Dutch rows across all
  vector groups, with `occurrenceStatus` PRESENT or ABSENT.
- Access: Darwin Core Archive `https://www.gbif.se/ipt/archive.do?r=vectordist_2026`
  (`dwca-vectordist_2026-v1.2.zip`). The ingester keeps Culicidae only and drops person-related
  identifier columns (`recordedByIDs`, `identifiedByIDs`).
- Use: the "expected species here" filter in the attribution rule engine, and the invasive
  watch-list mart.

## 5. Open-Meteo

- Forecast and historical weather APIs with no key. The free tier is for **non-commercial** use:
  fewer than 10,000 calls/day, 5,000/hour and 600/minute. Data is CC BY 4.0 and must be credited
  as "Weather data by Open-Meteo.com" with a link.
- Use: hourly air temperature for frequency normalisation when a sensor has no thermometer, plus
  humidity, wind and precipitation as covariates and simulator drivers. Calls are batched per
  site and cached (ETag and a local cache) so the platform stays far below the limits.

## 6. NUTS 2024 boundaries (Eurostat GISCO)

- Used once per sensor site to find its NUTS3 code (point-in-polygon in DuckDB spatial).
- The geometries are copyrighted (EuroGeographics) and come with usage provisions. They are
  **downloaded at runtime and never committed**. Milestone M9 confirms the exact NUTS 2024
  acknowledgement text from the GISCO metadata before release.

## 7. Own recordings

AudioMoth SD-card dumps and the live microphone go through the same edge pipeline. The speech
guard runs first, raw audio is not written to disk by default, and only features and events
leave the device (ADR-0008).

## What we deliberately do not use

| Candidate | Why not |
| :-- | :-- |
| Human case data (e.g. West Nile virus surveillance tables) | Health data; out of scope by policy. |
| Citizen-science observation records with observer names | Personal data; facet counts give us what we need. |
| HumBugDB `background` / `audio` clips and `field` clips | May contain human speech. |
| Kaggle "Wingbeats" optical dataset | Needs an account, and the whole archive is several GB. |
| Freesound or Xeno-canto sound searches | Needs keys, carries uploader identities, and mosquito coverage is sparse. |

## Attribution text (shown in the UI and the docs footer)

> Mosquito reference recordings: HumBugDB (Kiskin et al. 2021), CC BY 4.0. Species presence:
> GBIF.org and VectorNet (ECDC/EFSA), CC BY 4.0. Weather data by Open-Meteo.com, CC BY 4.0.
> Administrative boundaries: © EuroGeographics, source: European Commission – Eurostat/GISCO.
