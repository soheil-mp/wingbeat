# Technology landscape and stack selection

> Status: research note behind the ADRs in `docs/adr/`. Versions and project health were checked
> on PyPI, Docker Hub and GitHub releases on 2 November 2026. Renovate keeps pins current once
> code exists.

## Selection criteria

1. **Licence:** OSI-approved and MIT-compatible for anything imported. Copyleft or
   source-available servers only as separate containers, and only when no equal permissive
   option exists.
2. **Health:** a release in the last 6 months and an active maintainer base.
3. **Footprint:** the whole stack must run on one 16 GB laptop through Compose profiles.
4. **Standard interfaces:** S3, Kafka protocol, MQTT 5, OpenTelemetry, SQL, so any one part can be
   swapped.
5. **Testability:** each component can run in Testcontainers or Compose inside CI.

## Chosen stack

| Concern | Choice | Version (2026-11-02) | Licence | Why |
| :-- | :-- | :-- | :-- | :-- |
| Language | Python | 3.13 | PSF | `dagster-dbt` 0.29 still requires Python < 3.14, so 3.13 is the newest version the whole workspace supports. |
| Packaging | uv workspaces | 0.13.x | MIT/Apache-2.0 | One lockfile for a monorepo, fast CI, reproducible installs. |
| Lint and format | Ruff | 0.17 | MIT | One tool replaces flake8, isort and black. |
| Types | mypy (strict) | 2.4 | MIT | Mature. `ty` is still 0.0.x, so we try it later. |
| Tests | pytest, Hypothesis, pytest-benchmark, mutmut, Testcontainers | 9.2 / 6.170 / 5.3 / 3.8 / 4.15 | MIT / MPL-2.0 / BSD / BSD / Apache-2.0 | Property-based tests suit DSP. Mutation testing guards the estimators. |
| DSP | NumPy, SciPy, soundfile | 2.5 / 1.18 / 0.14 | BSD | Classical signal processing; no learned components. |
| Edge transport | Eclipse Mosquitto (MQTT 5) | 2.1 | EPL-2.0/EDL-1.0 | The reference MQTT broker; small enough for a Pi. |
| MQTT client | aiomqtt | 2.5 | BSD-3 | asyncio client on top of paho-mqtt. |
| Event log | Apache Kafka (KRaft) | 4.4 | Apache-2.0 | ZooKeeper-free since 4.0, with the official `apache/kafka` image. Chosen over Redpanda (BSL). |
| Schema registry | Apicurio Registry | 3.3 | Apache-2.0 | Confluent-compatible API without the Confluent Community Licence. |
| MQTT → Kafka bridge | Bento | 1.22 | MIT | Declarative, tested connector config. A small custom Python bridge is the fallback (ADR-0003). |
| Serialisation | Protocol Buffers + Buf | buf 1.75 | Apache-2.0 | Compact on the wire for the edge, plus `buf lint` and `buf breaking` gates in CI. |
| Stream processing | Quix Streams | 3.28 | Apache-2.0 | Python-native, stateful windows, exactly-once, Kafka-native. Bytewax's last release was in November 2024. |
| Hot store | ClickHouse | 26.10 | Apache-2.0 | Sub-second aggregates, Kafka table engine, TTLs, materialised views. |
| Object store | SeaweedFS (S3 API) | 4.52 | Apache-2.0 | The MinIO community repository was archived in April 2026 after image distribution stopped in October 2025. |
| Lakehouse format | DuckLake on DuckDB | DuckLake 1.0 / DuckDB 2.0 | MIT | SQL catalog (Postgres), Parquet on S3, ACID and time travel, no JVM. 1.0 was declared production-ready in April 2026. |
| Metadata DB | PostgreSQL | 18 | PostgreSQL | DuckLake catalog, Dagster storage, Apicurio storage. |
| Orchestration | Dagster | 1.13 | Apache-2.0 | Asset-centric, partitions and backfills, asset checks, dbt integration. |
| Transformation | dbt-core + dbt-duckdb | 1.12 / 1.11 | Apache-2.0 | Industry standard; model contracts and unit tests. |
| Data quality | dbt tests, Pandera, Dagster asset checks, datacontract-cli (ODCS v3) | — / 0.35 / — / 1.2 | Apache-2.0 / MIT / Apache-2.0 / MIT | Checks at each layer, contracts executable in CI. Soda Core 4 is under a proprietary licence. |
| Lineage | OpenLineage (+ Marquez UI, optional) | 1.55 | Apache-2.0 | Open standard. Marquez's last release was in October 2024, so the UI is optional. |
| API | FastAPI + Uvicorn | 0.162 / 0.54 | MIT / BSD | OpenAPI 3.1 out of the box, Server-Sent Events for the live feed. |
| Web UI | TypeScript, Vite, MapLibre GL | MapLibre 6.16 | BSD-3 | Light, no heavy framework. MapLibre is the open fork of Mapbox GL. |
| Telemetry | OpenTelemetry SDK + Collector | 1.45 / 0.164 | Apache-2.0 | Vendor-neutral traces, metrics and logs. |
| Metrics, logs, traces | Prometheus, Loki, Tempo, Grafana | 3.15 / 3.7 / 3.1 / 13.3 | Apache-2.0 / AGPL-3.0 (Loki, Tempo, Grafana) | The de-facto open observability stack. AGPL parts run as separate containers only. |
| Containers | Docker Buildx, multi-arch (amd64 + arm64) | Docker 29 | Apache-2.0 | arm64 for Raspberry Pi edge nodes. |
| Supply chain | Syft (SBOM), Cosign (keyless signing), GitHub attestations | 1.56 / 3.1 | Apache-2.0 | Signed, attested images on GHCR. |
| Releases | release-please + Conventional Commits | 17.11 | Apache-2.0 | Changelog and semver from history. |
| Dependencies | Renovate (Dependabot as fallback) | 44.x | AGPL-3.0 (hosted app) | Grouped updates with lockfile maintenance. |
| Kubernetes (local) | kind | 0.33 | Apache-2.0 | Conformant multi-node clusters in Docker. |
| Packaging for k8s | Helm | 4.3 | Apache-2.0 | Charts for our services and the upstream operators. |
| GitOps | Argo CD | 3.5 | Apache-2.0 | App-of-apps, drift detection. |
| Operators | Strimzi (Kafka), CloudNativePG, Altinity ClickHouse operator | 1.3 / 1.30 / 0.27 | Apache-2.0 | Declarative stateful services. |
| Autoscaling | KEDA | 2.21 | Apache-2.0 | Scales stream processors on Kafka consumer lag. |
| Secrets | SOPS + age (or Sealed Secrets) | 3.13 / 0.41 | MPL-2.0 / Apache-2.0 | Encrypted secrets in Git, no plaintext. |
| IaC | OpenTofu | 1.13 | MPL-2.0 | Open Terraform fork for the cluster bootstrap and GitHub settings. |
| Fault injection | Toxiproxy | 2.13 | MIT | Network faults between edge and broker in tests. |
| API contract tests | Schemathesis | 4.33 | MIT | Property-based tests generated from the OpenAPI spec. |
| Load tests | Locust | 2.47 | MIT | Python-native load profiles. |
| Docs | MkDocs Material | 9.8 | MIT | Stable today, but its build output announces end of life on 5 May 2027. Its successor Zensical is still 0.0.x; migrate before that date (stretch S8). |
| Task runner | just | 1.59 | CC0 | Readable recipes and cross-platform. |
| Secret scanning | gitleaks | 8.30 | MIT | Pre-commit and CI full-history scan. |

## Considered and rejected

| Option | Reason |
| :-- | :-- |
| MinIO | Community edition archived (April 2026). Images and binaries stopped in October 2025. |
| Redpanda | Business Source Licence; Kafka 4 now matches its simple single-binary ops. |
| Confluent Schema Registry | Confluent Community Licence (not OSI). |
| Bytewax | No release since November 2024. |
| Apache Flink / PyFlink | Excellent but JVM-heavy for a laptop. Revisit if throughput needs it (stretch S4). |
| RisingWave | Strong streaming SQL, but it adds a second SQL engine next to ClickHouse. |
| Apache Iceberg + Lakekeeper | Valid; DuckLake is simpler for one node. DuckLake 1.0 adds Iceberg-compatible bucket partitioning and deletion buffers, and an Iceberg export is stretch S5. |
| TimescaleDB | Compression and continuous aggregates are under the Timescale Licence, not OSI. |
| Airflow 3 | Task-centric. Dagster's asset model and asset checks fit data products better. |
| SQLMesh | Good. dbt has the wider ecosystem and adapter coverage, which is the more transferable skill. |
| Great Expectations | Overlaps with dbt tests + Pandera + asset checks. A third DQ framework adds weight without coverage. |
| Soda Core 4 | PyPI lists a proprietary licence. |
| `ty` type checker | Still 0.0.x. |
| Zensical | Still 0.0.x. |

## Risks to watch

- **DuckLake and DuckDB 2.0 are new.** Pin exact versions and keep the lake reproducible from
  Kafka replay plus reference sources, so a format change costs a rebuild, not data.
- **dagster-dbt and Python 3.14.** Move the workspace to 3.14 once `dagster-dbt` supports it.
  Renovate flags the change.
- **Marquez inactivity.** OpenLineage events are emitted regardless, so the UI can be swapped.
- **AGPL services** (Grafana, Loki, Tempo): used unmodified as separate containers and never
  vendored.
