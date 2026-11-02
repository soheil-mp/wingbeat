# 0006. ClickHouse for hot serving, DuckLake on S3 for the lakehouse

- Status: Accepted (validate in M4/M7)
- Date: 2026-11-02

## Context and problem statement

The platform needs (a) sub-second queries over the latest hours for live dashboards and the API,
and (b) a cheap, open, reproducible historical store for modelling and backfills. All of it must
fit in a small disk budget.

## Considered options

1. ClickHouse for everything.
2. ClickHouse (hot) + DuckLake on S3-compatible storage (cold).
3. PostgreSQL + TimescaleDB.
4. Apache Iceberg + REST catalog + Trino.

## Decision outcome

Chosen option 2.

- **ClickHouse 26.x** reads the enriched Kafka topic through the Kafka table engine and
  materialised views into MergeTree tables partitioned by day. Rollups use
  AggregatingMergeTree, and TTLs keep 30 days of raw rows.
- **DuckLake 1.0** keeps Parquet data on **SeaweedFS** (S3 API) with the catalog in
  **PostgreSQL 18**. dbt-duckdb builds the bronze → silver → gold models on it. Kafka offsets are
  written in the **same DuckLake transaction** as the data, which makes lake loading exactly-once
  and idempotent on retry.
- Storage budget: ≤ 2 GB total, checked by an asset check.

### Consequences

- Good: each store does what it is best at. The lake is open Parquet, so any engine can read it.
- Good: both stores can be rebuilt from Kafka replay plus reference sources.
- Bad: two query engines to operate. Data contracts keep them consistent, and a reconciliation
  check compares counts across Kafka, ClickHouse and DuckLake.

### Confirmation

M7 benchmarks: p95 under 200 ms for a 24 h activity query in ClickHouse. A full gold rebuild from
the lake in under 5 minutes on a laptop.
