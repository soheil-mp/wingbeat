# 0007. Protobuf event contracts with Buf and a schema registry

- Status: Accepted
- Date: 2026-11-02

## Context and problem statement

Events cross many boundaries: device → MQTT → bridge → Kafka → processors → stores. Breaking a
schema silently corrupts everything downstream.

## Considered options

1. JSON with JSON Schema.
2. Avro with a registry.
3. Protocol Buffers with Buf and a registry.

## Decision outcome

Chosen option 3. Schemas live in `schemas/wingbeat/<domain>/v1/*.proto`. CI runs `buf lint` and
`buf breaking` against `main`. Python code is generated with type stubs. **Apicurio Registry 3**
(Confluent-compatible API) stores the schemas with `BACKWARD_TRANSITIVE` compatibility, and Kafka
messages use the standard schema-ID framing. Data at rest is described by **Open Data Contract
Standard (ODCS) v3** contracts in `contracts/`, tested with `datacontract-cli`.

Every event carries an envelope: `event_id` (UUIDv7), `sensor_id`, `seq` (monotonic per
device), `event_time`, `ingest_time`, `schema_version`, `trace_parent`.

### Consequences

- Good: compact payloads for the edge (and nanopb for a future microcontroller port), with
  breaking changes caught before merge.
- Bad: generated code and a registry to run. Both are automated.

### Confirmation

A deliberately breaking change in a test branch fails CI.
