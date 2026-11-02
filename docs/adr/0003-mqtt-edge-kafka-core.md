# 0003. MQTT 5 at the edge, Apache Kafka in the core

- Status: Accepted (validate in M4)
- Date: 2026-11-02

## Context and problem statement

Sensors are small, intermittently connected devices. The platform needs durable, replayable
streams that several consumers (stream processor, hot store, lake ingestion) read independently.

## Considered options

1. Devices write to Kafka directly.
2. MQTT 5 broker at the edge, bridged into Kafka.
3. MQTT only, with consumers subscribing to the broker.

## Decision outcome

Chosen option 2. **Eclipse Mosquitto** handles device connections (persistent sessions, QoS 1,
Last Will for liveness, retained config messages, per-device ACLs). A **bridge** (Bento, with a
small custom Python bridge as fallback) forwards into **Apache Kafka 4 (KRaft)**. In Kafka,
partitioning by `sensor_id` keeps ordering per device, and retention allows replay.

### Consequences

- Good: the canonical IoT pattern, where each protocol does what it is best at. And yes, the
  broker is called Mosquitto.
- Good: Kafka replay lets us rebuild the hot store and the lake from the log.
- Bad: one more hop. The bridge must keep message identity and trace context (W3C
  `traceparent` in MQTT 5 user properties, then Kafka headers).

### Confirmation

M4 walking skeleton: p95 latency from device publish to Kafka under 200 ms locally. M5 chaos
test: a 10-minute broker outage loses zero events.
