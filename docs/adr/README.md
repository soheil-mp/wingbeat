# Architecture decision records

Decisions use the [MADR 4](https://adr.github.io/madr/) format. Copy `template.md`, take the
next number, and open a pull request. An accepted ADR is never edited in substance: supersede
it with a new one and link both ways.

| # | Decision | Status |
| :-- | :-- | :-- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-deterministic-signal-processing.md) | Deterministic, explainable signal processing; no machine learning | Accepted |
| [0003](0003-mqtt-edge-kafka-core.md) | MQTT 5 at the edge, Apache Kafka in the core | Accepted (validate in M4) |
| [0004](0004-python-uv-monorepo.md) | Python 3.13 monorepo with uv workspaces | Accepted |
| [0005](0005-dagster-orchestration.md) | Dagster for batch orchestration | Accepted (validate in M8) |
| [0006](0006-hot-and-cold-storage.md) | ClickHouse for hot serving, DuckLake on S3 for the lakehouse | Accepted (validate in M4/M7) |
| [0007](0007-protobuf-contracts.md) | Protobuf event contracts with Buf and a schema registry | Accepted |
| [0008](0008-privacy-by-design-audio.md) | Privacy by design: raw audio never leaves the device | Accepted |
| [0009](0009-temperature-normalised-attribution.md) | Temperature-normalised, candidate-set species attribution | Accepted (validate in M1/M2) |
| [0010](0010-synthetic-first-data.md) | Synthetic-first data with tightly capped real sources | Accepted |
