# SPI Payload Schema

**Status:** Pre-freeze approval baseline  
**Owner:** STM32 application data model and Raspberry Pi decoder  
**Boundary:** Application snapshots/events/diagnostics -> SPI frame payload

This document defines message payloads carried by the framing rules in [SPI_CONTRACT.md](SPI_CONTRACT.md). It does not define SPI electrical behavior or DMA ownership.

## Common Rules

- All fields are explicitly serialized little-endian.
- C structure padding is never transmitted.
- Payload length is the serialized byte count, not `sizeof()` of a C struct.
- Unknown message types, unsupported `protocol_version`, and unsupported payload `schema_version` values are rejected.
- A malformed payload must not modify application state.
- `frame_time_us` belongs to the outer frame and means frame assembly time.
- `measurement_timestamp_us` belongs to records and means acquisition time in the synchronized Pi time domain.
- `protocol_version` belongs to the outer frame and covers framing/transport compatibility.
- `schema_version` belongs to each payload and covers message layout compatibility.

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

Sensor record:

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

Motor record:

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

Initial sensor validity flags:

- bit 0: sample valid;
- bit 1: communication error;
- bit 2: magnet not detected;
- bit 3: magnet too weak;
- bit 4: magnet too strong;
- bit 5: timestamp synchronized;
- bits 6-15: reserved.

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

### TIME_SYNC (`0x12`)

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `reserved` | 1 |
| `flags` | 2 |
| `pi_time_us` | 8 |
| `sync_seq` | 4 |

The STM32 captures local monotonic time when processing the validated payload and updates its offset according to [SPI_CONTRACT.md](SPI_CONTRACT.md).

### ACK (`0x80`) and NACK (`0x81`)

| Field | Size |
| --- | ---: |
| `schema_version` | 1 |
| `request_type` | 1 |
| `status_code` | 2 |
| `request_seq` | 4 |
| `detail_code` | 4 |

NACK status codes must include invalid message, invalid length, CRC failure, invalid lifecycle state, and invalid time synchronization request.

### GET and Command Requests

`GET_SNAPSHOT`, `GET_STATUS`, and `GET_VERSION` contain a one-byte `schema_version` and reserved bytes set to zero. `SET_MOTOR_COMMAND` is not frozen until the Motor Service contract exists; it must not be implemented from this draft alone.

## Maximum Sizes

Contract v1.0 target:

```text
MAX_FRAME_BYTES = 512
MAX_PAYLOAD_BYTES = 490
```

`App/Inc/spi_payload_layout.h` is the machine-readable v1 layout authority. It fixes the outer header at 18 bytes, CRC at 4 bytes, payload maximum at 490 bytes, snapshot prefix at 12 bytes, and sensor/motor records at 24 bytes. For the six-sensor/eight-motor v1 target, payload size is `12 + (6 * 24) + (8 * 24) = 348` bytes and frame size is `18 + 348 + 4 = 370` bytes. The current application registers one provisional motor, which would use 180 payload bytes and a 202-byte frame; it is not final commissioning topology. The implementation must reject a payload that exceeds the maximum rather than truncate it. The maximum SPI clock remains the designated Raspberry Pi integration gate; DMA must support the fixed 512-byte frame limit.

The outer `protocol_version`, CRC-32/ISO-HDLC parameters, and payload `schema_version` have separate ownership. Protocol version changes cover framing/transport compatibility; schema version changes cover one message payload layout.

## Remaining Schema Decisions

- Exact event type and severity enumerations.
- Whether diagnostic counters are 32-bit or 64-bit on the wire.
- Snapshot dropped-count width and reset behavior.
- Whether future records use a tagged extension mechanism.
