# SPI Payload Schema

**Status:** Approved v1.0  
**Owner:** Message payload layouts between STM32 and Raspberry Pi  
**Scope:** Data structures and serialization rules for SPI frame payloads.

This document defines message payloads carried by the framing rules in [SPI_SYSTEM_INTERFACE.md](SPI_SYSTEM_INTERFACE.md). It does not define SPI electrical behavior, DMA ownership, or service implementation.

---

## Common Rules

- All fields are explicitly serialized **little-endian**.
- C structure padding is never transmitted.
- Payload length is the serialized byte count, not `sizeof()` of a C struct.
- Unknown message types, unsupported `protocol_version`, and unsupported payload `schema_version` values are rejected.
- A malformed payload must not modify application state.
- `frame_time_us` belongs to the outer frame and means frame assembly time.
- `measurement_timestamp_us` belongs to records and means acquisition time in the synchronized Pi time domain.
- `protocol_version` belongs to the outer frame and covers framing/transport compatibility (SPI_SYSTEM_INTERFACE.md).
- `schema_version` belongs to each payload and covers message layout compatibility.

---

## Message Payloads

### SNAPSHOT (`0x01`)

Fixed prefix:

| Offset | Size | Field |
| ---: | ---: | --- |
| 0 | 1 | `schema_version` |
| 1 | 1 | `sensor_count` |
| 2 | 1 | `motor_count` |
| 3 | 1 | `reserved` (must be zero) |
| 4 | 2 | `flags` |
| 6 | 2 | `dropped_snapshot_count_low` (diagnostic low word) |
| 8 | 4 | `response_to_seq` (request `seq`, or zero for asynchronous publication) |
| 12 | N | sensor records |
| 12+N | M | motor records |

The record counts determine the serialized lengths. The v1 target always serializes six sensor records for the configured six-axis topology; `sensor_count` is the number of serialized records, not the number of valid records. The initial motor maximum is eight records.

**Sensor record:**

| Offset | Size | Field |
| ---: | ---: | --- |
| 0 | 1 | `sensor_id` (logical axis 0-5) |
| 1 | 1 | `status` |
| 2 | 2 | `validity_flags` |
| 4 | 8 | `measurement_timestamp_us` |
| 12 | 2 | `raw_angle` |
| 14 | 4 | `processed_angle_mdeg` |
| 18 | 2 | `magnitude` |
| 20 | 1 | `agc` |
| 21 | 1 | `reserved` (must be zero) |
| 22 | 2 | `reserved_2` (must be zero) |

Sensor record size: 24 bytes.

**Motor record:**

| Offset | Size | Field |
| ---: | ---: | --- |
| 0 | 1 | `motor_index` |
| 1 | 1 | `status` |
| 2 | 2 | `validity_flags` |
| 4 | 2 | `can_id` |
| 6 | 1 | `command_code` |
| 7 | 1 | `payload_length` |
| 8 | 8 | `measurement_timestamp_us` |
| 16 | 8 | `payload` |

Motor record size: 24 bytes. Unused payload bytes must be zero. `payload_length` must not exceed eight.

**Initial sensor validity flags:**

- bit 0: sample valid;
- bit 1: communication error;
- bit 2: magnet not detected;
- bit 3: magnet too weak;
- bit 4: magnet too strong;
- bit 5: reserved (formerly timestamp synchronized; retired by ruling R16 and written zero);
- bit 6: not fitted (the axis has no encoder in the commissioning table; bit 0 is clear);
- bits 7-15: reserved.

**Sensor `status` byte (as built, recorded 2026-10-03):** the raw AS5600 STATUS register of the sample (MD magnet detected = bit 5, ML magnet too weak = bit 4, MH magnet too strong = bit 3; other bits zero). It is diagnostic; the normative validity of a record is carried by `validity_flags`. A record that has never held a sample carries 0.

**NOT_FITTED (added 2026-10-03, D-10):** an axis without an encoder in the commissioning table (SYSTEM_CONFIGURATION.md §2.1) is serialised at its stable logical ID with validity bit 6 set, bit 0 clear, bits 1-4 clear, `status` 0, and zero in `raw_angle`, `processed_angle_mdeg`, `magnitude` and `agc`; `measurement_timestamp_us` is the time the record was last refreshed. It is never a communication error and never a fault (SYS-ENC-002). This addition is compatible with schema v1 because bit 6 was reserved; `schema_version` stays 1. A decoder that predates it treats the record as not valid, which is acceptable.

**Stale records (added 2026-10-16, GitHub #80):** freshness is judged when the snapshot is copied. A sensor sample older than PRM-ACQ-07, or a motor position older than PRM-MOT-01, is sent with validity bit 0 clear and its last values and `measurement_timestamp_us` kept, so the host can see its age. Schema v1 has no stale bit; a dedicated one is a separate, versioned schema decision (for the motor record, ruling R10's bit set). A failed sensor read (bits 1-4) carries `status` but zero values and a zero timestamp.

**Motor validity flags and payload (as built, schema v1):** bit 0 feedback valid (a position has arrived and is not stale), bit 1 controller status valid (never set as built: no polled reply carries a drive status, so `status` is 0), bit 2 reserved (formerly timestamp synchronized, retired by R16), bits 3-15 reserved. `command_code` and `payload` are the last position reply: today the 30H reply the firmware polls (`0x30`, six bytes: big-endian int32 carry then uint16 value 0..0x3FFF, `payload_length` 6); speed and acknowledgements never replace them (R10). Ruling R10's 31H position, STALE and FAULT bits arrive with GitHub #61 (R11).

**Implementation status:** implemented on both sides (checked 2026-10-15: `SPI_SENSOR_VALIDITY_NOT_FITTED` in the firmware payload layout, `SENSOR_VALIDITY_NOT_FITTED` in the Pi decoder, decode tests in both suites); the outstanding NOT_FITTED behaviour test and tooling are GitHub #66 (LIVE-17). The firmware freshness state (`LatestValue_Freshness`: NONE, FRESH, STALE in `latest_value.h`) reaches the wire only as bit 0, as above. The shared golden snapshot (`shared/test-vectors/spi`) is what the latest-value store produces, asserted by both suites.

---

### EVENT (`0x02`)

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `event_type` | 1 |
| `severity` | 1 |
| `reserved` | 1 |
| `event_timestamp_us` | 8 |
| `source_id` | 2 |
| `detail_code` | 2 |
| `detail_value` | 4 |

Event types and severity values remain reserved for the error-handling contract; values must be assigned before implementation.

---

### DIAGNOSTIC (`0x03`)

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `health_level` | 1 |
| `reserved` | 2 |
| `diagnostic_timestamp_us` | 8 |
| `response_to_seq` | 4 |
| `lifecycle_state` | 1 |
| `time_sync_valid` | 1 |
| `reserved_2` | 2 |
| `fault_code` | 4 |
| `i2c_error_count` | 4 |
| `can_rx_error_count` | 4 |
| `can_tx_error_count` | 4 |
| `spi_dropped_frame_count` | 4 |

The diagnostic payload may be extended only by schema versioning or an explicitly reserved extension area.

**DIAGNOSTIC v2 (decided in [Issue #12](../../07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md) item 8; field layout not yet reconfirmed):** v2 is selected through explicit `schema_version` dispatch. A v1 decoder stays v1-only. v2 is requested by a new `GET_DIAGNOSTIC` request; today `GET_STATUS` returns only an ACK. The recommended v2 content keeps all v1 fields unchanged and adds the ClockSync field set: `sync_valid`, `sync_sample_count`, `rejected_sample_count`, `estimated_frequency_hz`, `estimated_frequency_error_ppm`, `reference_pi_time_us`, `reference_stm32_time_us`, `current_offset_us`, `min_half_rtt_us`, `last_sync_age_us`, `prediction_stddev_us`. In v2, `time_sync_valid` becomes a derived summary field.

---

### VERSION (`0x04`)

Solicited response to `GET_VERSION` (`0x14`). Identifies the firmware build that produced a frame, so that bench and integration evidence can be attributed to an exact firmware revision.

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `protocol_version` | 1 |
| `fw_version_major` | 1 |
| `fw_version_minor` | 1 |
| `fw_version_patch` | 1 |
| `build_flags` | 1 |
| `reserved` | 2 |
| `response_to_seq` | 4 |
| `git_hash_abbrev` | 4 |
| `commit_epoch_secs` | 4 |

Total payload: 20 bytes.

- `protocol_version` repeats the outer frame's transport version so a decoded payload is self-describing in a log.
- `build_flags` bit 0 is set when the firmware sources (`Arm_Sensor_Hub/` and `shared/`) had uncommitted changes at build time; the accompanying `git_hash_abbrev` then does not fully identify the source. Bits 1-7 are reserved and must be zero. **Timing and acceptance evidence recorded against a firmware reporting bit 0 set does not satisfy an integration gate.**
- `git_hash_abbrev` is the first eight hex digits of the commit hash read as a hexadecimal number, so commit `1a2b3c4d…` reports `0x1A2B3C4D` and a host formatting the field as eight lowercase hex digits reproduces `git rev-parse --short=8`. Zero when the build system could not determine it.
- `commit_epoch_secs` is the commit timestamp in seconds since the Unix epoch, not the build time, so the field stays reproducible across rebuilds of the same source. Zero when unavailable.

Adding this message type does not increment `protocol_version`: `0x04` was previously reserved, `VERSION` is emitted only in response to `GET_VERSION`, and no existing field meaning, ordering, or framing changes. A host that never sends `GET_VERSION` cannot observe any difference.

---

### TIME_SYNC (`0x12`)

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `reserved` | 1 |
| `flags` | 2 |
| `pi_time_us` | 8 |
| `sync_seq` | 4 |

**Deprecated** by [Issue #12](../../07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md). The STM32 no longer holds or applies an offset. Clock synchronization uses the `request_received_local_us` response extension below. This payload is retained only until the Issue #12 implementation removes the message.

### Clock-sync response extension (Issue #12 item 1)

Every response that contributes a ClockSync observation carries `request_received_local_us` (64-bit STM32 local time of request receipt; see `TIME_SYSTEM_INTERFACE.md` §3) through a versioned payload extension. Diagnostic-only responses do not carry it. `frame_time_us` is unchanged.

---

### ACK (`0x80`) and NACK (`0x81`)

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `request_type` | 1 |
| `status_code` | 2 |
| `request_seq` | 4 |
| `detail_code` | 4 |

NACK status codes must include invalid message, invalid length, CRC failure, invalid lifecycle state, and invalid time synchronization request.

---

### GET and Command Requests

`GET_SNAPSHOT`, `GET_STATUS`, and `GET_VERSION` contain a one-byte `schema_version` and reserved bytes set to zero. `GET_VERSION` is answered with a `VERSION` (`0x04`) frame; `GET_SNAPSHOT` is answered with `SNAPSHOT` when one is staged, and the remaining requests are answered with `ACK`/`NACK`.

### SET_MOTOR_COMMAND (`0x13`) — frozen 2026-10-03 for single gated commands

One command for one motor. Trajectories are not part of this message (charter non-goal).

| Offset | Size | Field |
| ---: | ---: | --- |
| 0 | 1 | `schema_version` (1) |
| 1 | 1 | `motor_index` |
| 2 | 1 | `command` |
| 3 | 1 | `reserved` (must be zero) |
| 4 | 4 | `value` (int32, little-endian) |
| 8 | 4 | `reserved_2` (must be zero) |

Total payload: 12 bytes.

| `command` | Name | `value` |
| ---: | --- | --- |
| 0x01 | ENABLE | unused, zero |
| 0x02 | DISABLE | unused, zero |
| 0x03 | STOP | unused, zero; controlled stop |
| 0x04 | MOVE_TO_POSITION | target joint position in processed millidegrees, the same unit as the snapshot's `processed_angle_mdeg` |
| 0x05 | MOVE_AT_VELOCITY | signed velocity in the unit of the MKS speed command (see [`icm-project/references/mks-servo42d-57d-can/`](../../../icm-project/references/mks-servo42d-57d-can/)). **Provisional:** the unit is fixed when LIVE-20 is implemented. |

**Response:** ACK when the motion gate (SYS-GATE-001) accepts the command and it is queued to CAN. Otherwise NACK with `status_code` = INVALID_STATE and `detail_code` = the gate reason:

| `detail_code` | Gate reason |
| ---: | --- |
| 0 | ALLOWED |
| 1 | LIFECYCLE_NOT_ACTIVE |
| 2 | PREREQUISITE_INVALID |
| 3 | PREREQUISITE_LATCHED |
| 4 | MOTOR_NOT_READY |

These are the `MotionPermission_Reason` values in `motion_permission.h` as of 2026-10-03 and must stay in lockstep with it. ACK means accepted, not executed; completion is observed in the snapshot motor record.

**Mapping to MKS:** each command maps to one MKS CAN command, named by reference to the manual extract in `icm-project/references/mks-servo42d-57d-can/` and not restated here: ENABLE to the enable command, DISABLE to the disable command, STOP to the stop command, MOVE_TO_POSITION to the absolute position command, and MOVE_AT_VELOCITY to the speed command.

**Implementation status:** not implemented on either side (2026-10-03); tracked as the lockstep issue '[LIVE-20] Implement SET_MOTOR_COMMAND path (C, Python, tests)'.

---

## Maximum Sizes

Contract v1.0 target:

```text
MAX_FRAME_BYTES = 512
MAX_PAYLOAD_BYTES = 490
```

The machine-readable v1 layout authority fixes the outer header at 18 bytes, CRC at 4 bytes, payload maximum at 490 bytes, snapshot prefix at 12 bytes, and sensor/motor records at 24 bytes. For the six-sensor/eight-motor v1 target, payload size is `12 + (6 * 24) + (8 * 24) = 348` bytes and frame size is `18 + 348 + 4 = 370` bytes. The current application may register provisional motors; final commissioning topology is pending. The implementation must reject a payload that exceeds the maximum rather than truncate it. The maximum SPI clock remains the designated Raspberry Pi integration gate; DMA must support the fixed 512-byte frame limit.

The outer `protocol_version`, CRC-32/ISO-HDLC parameters, and payload `schema_version` have separate ownership. Protocol version changes cover framing/transport compatibility; schema version changes cover one message payload layout.

---

## Remaining Schema Decisions

- Exact event type and severity enumerations.
- Whether diagnostic counters are 32-bit or 64-bit on the wire.
- Snapshot dropped-count width and reset behavior.
- Whether future records use a tagged extension mechanism.
- Wire placement and version number of the `request_received_local_us` extension (Issue #12 item 1).
- `GET_DIAGNOSTIC` message value and field-by-field DIAGNOSTIC v2 layout (Issue #12 item 8).
- MOVE_AT_VELOCITY unit (Provisional until LIVE-20).

---

## Provenance

Reconciled from `docs/project/protocols/spi-payload-schema.md`.
