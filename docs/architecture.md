# Architecture

This is the target architecture. `ROADMAP.md` gives the order of construction, and `docs/adr/`
gives the reasons behind each choice.

## 1. System context

```mermaid
flowchart LR
    subgraph Field["Field (edge)"]
        S1["Acoustic sensor<br/>(Raspberry Pi + MEMS mic<br/>or AudioMoth importer)"]
        SIM["Sensor fleet simulator<br/>(virtual sensors)"]
    end
    subgraph Ext["Open data (no keys)"]
        OM["Open-Meteo<br/>hourly weather"]
        GB["GBIF<br/>species facets"]
        VN["VectorNet 2026<br/>NUTS3 status"]
        HB["HumBugDB on Zenodo<br/>range-read clips"]
        NU["GISCO NUTS 2024"]
    end
    WB(["Wingbeat platform"])
    U["Viewer<br/>(public read-only UI, Grafana, API)"]
    S1 -- "MQTT 5 + TLS<br/>features only" --> WB
    SIM -- "MQTT 5" --> WB
    OM & GB & VN & HB & NU -- "HTTPS (Dagster)" --> WB
    WB -- "REST, SSE, dashboards" --> U
```

## 2. Containers and data flow

```mermaid
flowchart TB
    subgraph Edge
        AG["edge-agent<br/>ring buffer → speech guard → DSP →<br/>events + telemetry, SQLite outbox"]
    end
    MQ[("Eclipse Mosquitto<br/>MQTT 5")]
    BR["bridge (Bento)<br/>MQTT → Kafka, keeps traceparent"]
    subgraph Kafka["Apache Kafka 4 (KRaft) + Apicurio Registry"]
        T1[["raw.detections.v1"]]
        T2[["raw.telemetry.v1"]]
        T3[["enriched.detections.v1"]]
        T4[["alerts.v1"]]
        T5[["ref.weather.v1 / ref.sensors.v1 (compacted)"]]
        DLQ[["dlq.v1"]]
    end
    SP["stream-processor (Quix Streams)<br/>validate · dedupe · enrich · normalise ·<br/>attribute · window · alert"]
    CH[("ClickHouse<br/>hot: 30 days, rollups")]
    subgraph Lake["Lakehouse"]
        DL[("DuckLake catalog<br/>PostgreSQL 18")]
        S3[("SeaweedFS S3<br/>Parquet bronze/silver/gold")]
    end
    DG["Dagster<br/>reference ingests · Kafka→lake ·<br/>dbt · asset checks · retention"]
    DBT["dbt-duckdb models<br/>+ tests + contracts"]
    API["api (FastAPI)<br/>REST + SSE"]
    UI["web UI<br/>map, live feed, explanations"]
    GF["Grafana<br/>ops · science · data quality"]
    OBS["OTel Collector → Prometheus · Loki · Tempo"]

    AG -- "QoS 1" --> MQ --> BR --> T1 & T2
    T1 & T2 & T5 --> SP
    SP --> T3 & T4 & DLQ
    T3 & T4 & T2 --> CH
    T1 & T2 & T3 --> DG --> DL & S3
    DG --> DBT --> DL
    DG -- "weather, sensors" --> T5
    CH --> API --> UI
    T3 --> API
    CH --> GF
    AG & BR & SP & API & DG -. "OTLP" .-> OBS --> GF
```

## 3. Event lifecycle and guarantees

| Stage | Guarantee | Mechanism |
| :-- | :-- | :-- |
| Device → broker | at-least-once, survives outages | MQTT QoS 1, persistent session, SQLite WAL outbox with bounded size and backoff |
| Broker → Kafka | at-least-once, ordered per sensor | bridge keyed by `sensor_id`, idempotent producer, `acks=all` |
| Kafka → processor → Kafka | exactly-once | Quix Streams transactional processing; dedupe on `event_id` with a TTL state store |
| Kafka → ClickHouse | effectively-once | Kafka engine plus `ReplacingMergeTree` on `event_id` |
| Kafka → lake | exactly-once | offsets committed in the same DuckLake transaction as the rows |
| Late data | accepted up to the grace period | event-time windows with a watermark and a 10-minute grace; later events go to a `late` table, never dropped silently |

Reconciliation: a Dagster asset check compares per-hour counts across Kafka offsets, ClickHouse
and DuckLake and fails on drift over 0.1 %.

## 4. Medallion layers (DuckLake)

| Layer | Content | Built by |
| :-- | :-- | :-- |
| bronze | Raw decoded events and telemetry as received, plus reference snapshots | Dagster Kafka→lake asset (hourly partitions) |
| silver | Validated, deduplicated, typed, enriched (site, NUTS3, temperature), SCD2 sensor dimension | dbt staging and intermediate models, dbt snapshots |
| gold | `fct_detection`, `fct_activity_hourly`, `fct_sensor_uptime_daily`, `mart_invasive_watchlist`, `mart_frequency_vs_temperature`, `mart_data_completeness` | dbt marts with model contracts |

## 5. Topic and naming conventions

- Topics: `wingbeat.<layer>.<entity>.v<major>` (for example `wingbeat.raw.detections.v1`). Key
  is `sensor_id`; 6 partitions in development; retention 24 h, except compacted `ref.*` topics.
- MQTT: `wingbeat/v1/<site_id>/<sensor_id>/{detections|telemetry|status|config}`; `status`
  carries the Last Will, `config` is retained.
- Schemas: `schemas/wingbeat/<domain>/v1/*.proto`, package `wingbeat.<domain>.v1`.

## 6. Deployment views

| View | What runs | Used for |
| :-- | :-- | :-- |
| `compose --profile core` | Mosquitto, Kafka, Apicurio, bridge, stream-processor, ClickHouse, Grafana, simulator | Daily development, walking skeleton |
| `compose --profile batch` | + PostgreSQL, SeaweedFS, Dagster | Reference ingestion, lake, dbt |
| `compose --profile obs` | + OTel Collector, Prometheus, Loki, Tempo | Observability work |
| kind + Argo CD | Everything through Helm charts and operators (Strimzi, CloudNativePG, Altinity) | Platform milestone, GitOps, autoscaling, chaos |
| Raspberry Pi | edge-agent container + systemd unit | Hardware-in-the-loop |
