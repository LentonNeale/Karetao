# SPI Host Contract: Raspberry Pi <-> STM32F405

**Contract version:** 1.0 pre-freeze/approval baseline  
**Host:** Raspberry Pi SPI master and system time authority  
**Device:** STM32F405RGT6 SPI3 slave  
**Status:** Pre-freeze approval baseline

## 1. Purpose

This document defines the SPI transport, framing, transaction, timestamp, and synchronization contract between the Raspberry Pi and STM32 sensor hub. Payload layouts are owned by [spi-payload-schema.md](spi-payload-schema.md), and buffer ownership is owned by [Arm_Sensor_Hub/Documentation/SNAPSHOT_COHERENCY_CONTRACT.md](../../Arm_Sensor_Hub/Documentation/SNAPSHOT_COHERENCY_CONTRACT.md). It is independent of the STM32 SPI driver implementation.

The contract deliberately separates three concerns:

```text
SPI contract
├── Transport: SPI mode, framing, CRC, DMA, DATA_READY
├── Data model: snapshots, events, diagnostics, commands
└── Time model: TIME_SYNC, offset, validity, measurement timestamps
```

## 2. Roles and Physical Interface

| Role | Device |
| --- | --- |
| SPI master and time authority | Raspberry Pi |
| SPI slave, sensor hub, CAN interface | STM32F405 |
| Data availability signal | STM32 DATA_READY -> Raspberry Pi |

The Raspberry Pi initiates all SPI clocking. The STM32 asserts `DATA_READY` when a complete frame has been prepared, handed to DMA ownership, and the DMA transfer has been successfully armed; it then waits for the Raspberry Pi to assert NSS and clock the transaction.

Current STM32 SPI3 mapping:

| Signal | STM32 pin | Direction relative to STM32 |
| --- | --- | --- |
| NSS | PA15 | Input |
| SCK | PC10 | Input |
| MISO | PC11 | Output |
| MOSI | PC12 | Input |

Current implementation uses 8-bit, 2-line, hardware NSS, with DMA1 Stream 0 for RX and Stream 5 for TX. SPI mode is mode 0 (CPOL=0, CPHA=0). The STM32 SPI3 DMA path is implemented. The 5 MHz value remains the current integration ceiling and requires live-host and physical acceptance evidence before it is treated as an accepted maximum.

## 3. Protocol Rules

- All multi-byte integers are little-endian.
- Frames must be explicitly serialized and deserialized; C struct layout must never be sent directly.
- Every frame includes a `protocol_version`, message type, payload length, sequence number, and CRC32. Payloads include their own `schema_version` where defined by [spi-payload-schema.md](spi-payload-schema.md).
- `payload_len` excludes the fixed prefix and CRC.
- CRC32 uses CRC-32/ISO-HDLC: polynomial `0x04C11DB7`, initial `0xFFFFFFFF`, reflected input/output, final XOR `0xFFFFFFFF`, little-endian wire field. It covers the fixed header and payload, excluding the CRC field itself.
- Malformed frames must not modify application state.

`Crc32IsoHdlc_Compute()` is the sole firmware CRC-32/ISO-HDLC implementation. `Crc32IsoHdlc_WriteLittleEndian()` and `Crc32IsoHdlc_ReadLittleEndian()` encode and decode the four-byte wire field; `Crc32IsoHdlc_Verify()` compares that field with the computed header-plus-payload CRC.

Published v1 reference vectors:

| Input bytes | CRC-32/ISO-HDLC | Wire bytes |
| --- | --- | --- |
| empty | `0x00000000` | `00 00 00 00` |
| ASCII `123456789` | `0xCBF43926` | `26 39 F4 CB` |
| `5A A5 01 01 03 00 34 12 00 00 88 77 66 55 44 33 22 11 AA BB CC` | `0x049705F5` | `F5 05 97 04` |

## 4. Frame Format

This draft resolves the timestamp naming and header ambiguity by making `frame_time_us` part of the fixed frame prefix:

| Offset | Size | Field | Description |
| --- | ---: | --- | --- |
| 0 | 2 | `magic` | Fixed synchronization value `0xA55A`. |
| 2 | 1 | `protocol_version` | Framing/transport compatibility version, initially `1`. |
| 3 | 1 | `message_type` | Message type allocation below. |
| 4 | 2 | `payload_len` | Payload size in bytes. |
| 6 | 4 | `seq` | Monotonic transmitted-frame sequence number. |
| 10 | 8 | `frame_time_us` | Synchronized STM32 hub time at frame assembly. |
| 18 | N | `payload` | Message-specific payload. |
| 18+N | 4 | `crc32` | CRC32 over bytes `0 .. 17+N`. |

`frame_time_us` is not a measurement timestamp. It identifies the hub time when the frame was assembled. Individual physical measurements carry their own timestamps in the Raspberry Pi time domain.

## 5. Transaction Model

The protocol uses pipelined request/response transactions:

```text
Transaction N:   Pi sends request N; STM32 returns the response staged before N.
Between N/N+1:  STM32 validates request N and stages response N+1.
Transaction N+1: Pi receives response N+1 while sending request N+1.
```

The STM32 never initiates SPI clocking. The first response after boot is a defined status, ACK, or NACK frame. The outer `seq` identifies the transmitted frame itself. A solicited response carries `response_to_seq`, equal to the request frame's `seq`; `ACK` and `NACK` carry `request_seq`. Asynchronous publications use zero correlation according to their payload schema.

## 6. Message Types

| Value | Name | Direction | Purpose |
| ---: | --- | --- | --- |
| `0x01` | `SNAPSHOT` | STM32 -> Pi | Current coherent sensor and motor state. |
| `0x02` | `EVENT` | STM32 -> Pi | Asynchronous event. |
| `0x03` | `DIAGNOSTIC` | STM32 -> Pi | Diagnostic and lifecycle status. |
| `0x10` | `GET_SNAPSHOT` | Pi -> STM32 | Request current snapshot. |
| `0x11` | `GET_STATUS` | Pi -> STM32 | Request status. |
| `0x12` | `TIME_SYNC` | Pi -> STM32 | Update STM32-to-Pi time relationship. |
| `0x13` | `SET_MOTOR_COMMAND` | Pi -> STM32 | Send a motor command subject to lifecycle/safety checks. |
| `0x14` | `GET_VERSION` | Pi -> STM32 | Request firmware/protocol version. |
| `0x80` | `ACK` | STM32 -> Pi | Successful command acknowledgement. |
| `0x81` | `NACK` | STM32 -> Pi | Rejected command or malformed request. |

Unused values are reserved.

## 7. Sequence Numbers

Every transmitted frame has a 32-bit `seq`. It increments monotonically per transmitter and wraps naturally from `0xFFFFFFFF` to `0`. It identifies that frame, not an individual measurement and not necessarily the request it answers. Solicited responses use payload-specific `response_to_seq` or `request_seq` for correlation. Sensor records have independent measurement timestamps.

The Raspberry Pi uses sequence numbers to detect duplicates, missing frames, stale responses, and request/response mismatches. A sequence number must not be reused for simultaneously outstanding transactions.

## 8. DATA_READY

`DATA_READY` is an STM32-to-Pi transport-availability signal using the approved armed-then-assert model:

```text
LOW   = no complete response frame is currently armed for DMA transmission
HIGH  = a complete response frame has been handed to DMA ownership and the DMA transfer is armed
```

The frame being serialized is not sufficient to assert `DATA_READY`. A frame merely staged in a software buffer but not yet DMA-armed is not sufficient. Partial DMA activity is not sufficient. The production owner is `SpiSlaveService`; SensorTask never drives this GPIO.

The STM32 may deassert `DATA_READY` after the frame is consumed according to the acknowledgement policy. The signal does not identify the message type.

If a new snapshot replaces an unread response, the service increments a dropped/replaced counter and reports it through diagnostics.

The service's configurable 1 ms polling fallback rechecks staged-frame availability. When staged data is present while DATA_READY is low and no transfer is armed, the service re-arms the DMA transfer, reasserts DATA_READY, and reports poll-recovery and host-stall counters. A 100 ms host-stall timeout aborts the active DMA transfer and returns the service to a re-armable state. These software recovery paths have been exercised on the STM32 target, but the physical DATA_READY waveform and Pi-side GPIO path remain unvalidated.

## 9. Snapshot Coherency and Ownership

A `SNAPSHOT` is a logically coherent view of the available STM32 state. For the intended six-joint stream, one snapshot should contain all available joint records and associated CAN motor records.

The snapshot builder owns serialization from producer-owned latest-value caches into a free SPI frame buffer:

```text
SensorTask -> sensor cache ----┐
                               ├-> Snapshot Builder -> free SPI frame buffer -> DMA
CAN service -> motor cache ----┘
```

The SPI service owns two static serialized frame buffers. SensorTask and CAN service never write those buffers. The ownership operation must be bounded and protected against task/DMA concurrency. Replace-if-new is permitted only when a free buffer exists; no DMA-owned buffer may be overwritten.

## 10. Measurement Timestamps

Every physical measurement carries its own acquisition timestamp. A measurement timestamp represents the synchronized hub-time estimate corresponding to when the measurement was acquired. It does not represent frame assembly time or Raspberry Pi reception time.

Minimum sensor record concept:

```text
sensor_id
status
measurement_timestamp_us
raw_value
processed_value
```

Minimum motor record concept:

```text
motor_index
can_id
command_code
status
measurement_timestamp_us
payload
```

The exact record schema is a separate data-model decision and must be frozen before the encoder is implemented.

## 11. Time Domain

The Raspberry Pi is the system time authority. The STM32 maintains a monotonic local clock and does not reset that clock during synchronization.

```text
hub_time_us = local_time_us + time_offset_us
time_offset_us = pi_time_us - stm32_local_time_us
```

Exported sensor and motor timestamps use `hub_time_us`. The raw local monotonic clock remains an internal timing source. The transport timestamp `frame_time_us` must not replace measurement timestamps.

## 12. TIME_SYNC

`TIME_SYNC` is a Raspberry Pi-to-STM32 message with this payload:

| Field | Type | Description |
| --- | --- | --- |
| `pi_time_us` | `uint64_t` | Pi time associated with the defined synchronization point. |
| `sync_seq` | `uint32_t` | Monotonic synchronization sequence. |
| `flags` | `uint16_t` | Synchronization/control flags. |

When the STM32 processes the message it captures `t_stm32` from its local monotonic clock and calculates:

```text
time_offset_us = pi_time_us - t_stm32
```

The STM32 stores:

```text
time_sync_valid
time_offset_us
last_sync_sequence
last_sync_local_time_us
```

An update is accepted only after frame, version, payload, and sequence validation. The update must be committed atomically from task context. The previous offset remains valid until a newer accepted update replaces it.

The initial contract treats `pi_time_us` as the Pi time associated with the synchronization transaction. This includes one-way transport uncertainty. A future two-way exchange may add Pi `t1`/`t3` and STM32 `t2` timestamps to estimate round-trip delay and offset more accurately. That is a versioned enhancement, not a requirement for the first implementation.

## 13. Synchronization Validity and Monotonicity

The v1 synchronization validity timeout is 5 seconds. When the timeout expires:

```text
local monotonic clock continues
hub-time calculation continues
 time_sync_valid = false
```

The STM32 must not claim synchronized timestamps while `time_sync_valid` is false. Status/diagnostic messages must expose synchronization validity and, where useful, age since the last accepted update.

The first implementation may step the offset directly. If repeated updates cause undesirable timestamp discontinuities, a later contract revision may define filtered or slewed offset correction. The implementation must keep raw local time distinct from exported synchronized hub time.

## 14. Host Responsibilities

The Raspberry Pi shall:

- operate as SPI master;
- observe `DATA_READY`;
- validate magic, version, length, and CRC32;
- track sequence numbers;
- reject stale and duplicate responses;
- periodically issue `TIME_SYNC`;
- maintain the authoritative system clock;
- timestamp measurements received directly through other interfaces;
- correlate measurements using the common time domain;
- never use SPI reception time as measurement time.

## 15. STM32 Responsibilities

The STM32 shall:

- operate SPI3 as a slave;
- use DMA with minimal ISR/callback work;
- maintain a monotonic local clock and Pi-derived offset;
- timestamp measurements at acquisition;
- maintain snapshot coherency and explicit buffer ownership;
- assert `DATA_READY` only after a complete frame is DMA-armed;
- validate incoming frames before changing state;
- maintain frame and synchronization sequence numbers;
- report synchronization validity;
- apply lifecycle and safety rules to incoming commands.

## 16. Error Handling

Reject a frame when magic, version, message type, length, CRC, sequence, or lifecycle permission is invalid. Where practical, return `NACK` with an error code such as:

- `INVALID_MAGIC`
- `UNSUPPORTED_VERSION`
- `INVALID_LENGTH`
- `CRC_ERROR`
- `INVALID_MESSAGE`
- `INVALID_STATE`
- `TIME_SYNC_INVALID`

A malformed or rejected frame must not modify application state. Recoverable transport faults may be retried or reported without changing lifecycle state; persistent DMA/NSS/transport faults follow the system lifecycle contract and may enter `ERROR`.

## 16. Lifecycle Integration

Normal sensor snapshots require the SPI service and sensor dependencies to be operational. `TIME_SYNC` may be accepted whenever the SPI transport is configured and able to receive valid commands, even if normal publication is not `ACTIVE`. Motor commands require CAN availability and must obey the lifecycle safety gate.

See [Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md](../../Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md) for canonical state semantics and transition rules.

## 17. Versioning and Remaining Integration Gate

Any incompatible change to field meaning/order, timestamp semantics, framing, CRC, or message semantics requires a protocol version increment.

DMA implementation is no longer a remaining work item. The remaining SPI integration gate is live-host and physical acceptance of the implemented transport, including:

- maximum 5 MHz clock acceptance and associated DMA timing;
- NSS behavior and abort/recovery behavior under a real master;
- DATA_READY electrical timing and Raspberry Pi GPIO behavior;
- GPIO/SCK/MISO signal integrity;
- sustained and repeated 512-byte transactions;
- real Raspberry Pi <-> STM32 request/response behavior and sequence/correlation handling.

The current 5 MHz value is an integration ceiling, not hardware approval.

The following are approved v1.0 decisions and must not be redefined by lower-level documents: mode 0; 512-byte maximum frame; 490-byte maximum payload; CRC-32/ISO-HDLC parameters; pipelined request/response; five-second synchronization validity; one-way TIME_SYNC transaction-point estimate; direct offset stepping; producer-cache/Snapshot-Builder/two-frame ownership; fixed six-record sensor snapshots; and replace-if-new behavior with drop diagnostics.
- lifecycle states permitted for each message type.

## 18. Contract Invariants

1. Raspberry Pi is the system time authority.
2. STM32 local time is monotonic and is never reset by synchronization.
3. Exported timestamps use local time plus the current accepted offset.
4. Measurement timestamps represent acquisition time, not transport time.
5. `frame_time_us` represents frame assembly time, not measurement time.
6. A snapshot is internally coherent.
7. An SPI-owned DMA buffer cannot be modified during transmission.
8. CRC failure cannot modify application state.
9. Every frame has a sequence number.
10. `DATA_READY` is asserted only for a complete available frame whose DMA transfer is armed.
11. Loss of synchronization is explicitly reported through `time_sync_valid`.
12. Timestamp correlation uses the shared Pi time domain.
