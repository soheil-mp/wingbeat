# 0005. Dagster for batch orchestration

- Status: Accepted (validate in M9)
- Date: 2026-11-02

## Context and problem statement

Batch work includes reference ingestion (weather, species presence, regions, reference clips),
Kafka-to-lake loading, dbt transformations, data-quality checks, compaction and retention.
These are **data products** with freshness expectations, not just tasks.

## Considered options

1. Dagster (asset-centric).
2. Apache Airflow 3 (task-centric, now with assets).
3. Kestra (YAML-first).
4. Cron + scripts.

## Decision outcome

Chosen option 1, **Dagster 1.13**: software-defined assets with partitions (daily × site) and
backfills, asset checks for data quality, freshness policies, sensors for new upstream versions,
concurrency pools for rate-limited APIs, and first-class dbt integration. It runs locally with
`dg dev` and in Kubernetes with the official Helm chart.

### Consequences

- Good: lineage, quality and freshness show in one place, and backfills are a first-class
  operation.
- Bad: Dagster's daemon and webserver add memory. They sit in the `batch` Compose profile.

### Confirmation

M9: every external source is an asset with at least one blocking asset check and a freshness
policy.
