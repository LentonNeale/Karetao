# SPI System Interface

**Contract version:** 1.0  
**Host:** Raspberry Pi SPI master and system time authority  
**Device:** STM32F405RGT6 SPI3 slave  
**Scope:** Transport, framing, transaction, timestamp, and synchronization contract between Raspberry Pi and STM32 sensor hub.

## Authority

This document defines the Karetao system-level SPI contract: externally visible framing, transaction ownership, timing, and data semantics. Component repositories own SPI driver/service implementation details (DMA mechanics, HAL integration, buffer pool internals, task scheduling).

---

## 1. Roles and Physical Interface

| Role | Device |
| --- | --- |
| SPI master and time authority | Raspberry Pi |
| SPI slave, sensor hub, CAN interface | STM32F405 |
| Data availability signal | STM32 DATA_READY → Raspberry Pi |

The Raspberry Pi initiates all SPI clocking and is the system time authority. The STM32 asserts `DATA_READY` when a complete frame has been prepared and the DMA transfer has been successfully armed; it then waits for the Raspberry Pi to assert NSS and clock the transaction.

Current STM32 SPI3 mapping:

| Signal | STM32 pin | Direction |
| --- | --- | --- |
| NSS | PA15 | Input |
| SCK | PC10 | Input |
| MISO | PC11 | Output |
| MOSI | PC12 | Input |

SPI mode: **Mode 0** (CPOL=0, CPHA=0). The current 5 MHz value is an integration ceiling, not hardware approval.

---

## 2. Protocol Rules

- All multi-byte integers are **little-endian**.
- Frames must be explicitly serialized and deserialized; C struct layout must never be sent directly.
- Every frame includes a `protocol_version`, message type, payload length, sequence number, and CRC32.
- `payload_len` excludes the fixed header (18 bytes) and CRC (4 bytes).
- CRC-32/ISO-HDLC: polynomial `0x04C11DB7`, initial `0xFFFFFFFF`, reflected input/output, final XOR `0xFFFFFFFF`, little-endian wire field. It covers the fixed header and payload, excluding the CRC field itself.
- Malformed frames must not modify application state.

**CRC-32/ISO-HDLC reference vectors:**

| Input bytes | CRC-32/ISO-HDLC | Wire bytes |
| --- | --- | --- |
| empty | `0x00000000` | `00 00 00 00` |
| ASCII `123456789` | `0xCBF43926` | `26 39 F4 CB` |
| `5A A5 01 01 03 00 34 12 00 00 88 77 66 55 44 33 22 11 AA BB CC` | `0x049705F5` | `F5 05 97 04` |

---

## 3. Frame Format

| Offset | Size | Field | Description |
| --- | ---: | --- | --- |
| 0 | 2 | `magic` | Fixed synchronization value `0xA55A`. |
| 2 | 1 | `protocol_version` | Framing/transport compatibility version, initially `1`. |
| 3 | 1 | `message_type` | Message type allocation (§6 below). |
| 4 | 2 | `payload_len` | Payload size in bytes. |
| 6 | 4 | `seq` | Monotonic transmitted-frame sequence number. |
| 10 | 8 | `frame_time_us` | Synchronized STM32 hub time at frame assembly. |
| 18 | N | `payload` | Message-specific payload (details in SPI_PAYLOAD_SCHEMA.md). |
| 18+N | 4 | `crc32` | CRC32 over bytes 0 through 17+N. |

**Fixed transaction frame: 512 bytes total.** Maximum payload: 490 bytes.

`frame_time_us` is not a measurement timestamp. It identifies the hub time when the frame was assembled. Individual physical measurements carry their own timestamps in the Raspberry Pi time domain.

---

## 4. Transaction Model

The protocol uses **pipelined request/response transactions**:

```text
Transaction N:   Pi sends request N; STM32 returns the response staged before N.
Between N/N+1:  STM32 validates request N and stages response N+1.
Transaction N+1: Pi receives response N+1 while sending request N+1.
```

The STM32 never initiates SPI clocking. The first response after boot is a defined status, ACK, or NACK frame. The outer `seq` identifies the transmitted frame itself. A solicited response carries `response_to_seq`, equal to the request frame's `seq`; ACK and NACK carry `request_seq`. Asynchronous publications use zero correlation according to their payload schema.

**Request/response ownership is deterministic** (SD-15).

---

## 5. Message Types

| Value | Name | Direction | Purpose |
| ---: | --- | --- | --- |
| `0x01` | `SNAPSHOT` | STM32 → Pi | Current coherent sensor and motor state. |
| `0x02` | `EVENT` | STM32 → Pi | Asynchronous event. |
| `0x03` | `DIAGNOSTIC` | STM32 → Pi | Diagnostic and lifecycle status. |
| `0x04` | `VERSION` | STM32 → Pi | Firmware and protocol version report, solicited by `GET_VERSION`. |
| `0x10` | `GET_SNAPSHOT` | Pi → STM32 | Request current snapshot. |
| `0x11` | `GET_STATUS` | Pi → STM32 | Request status. |
| `0x12` | `TIME_SYNC` | Pi → STM32 | Update STM32-to-Pi time relationship. |
| `0x13` | `SET_MOTOR_COMMAND` | Pi → STM32 | Send a motor command subject to lifecycle/safety checks. |
| `0x14` | `GET_VERSION` | Pi → STM32 | Request firmware/protocol version. |
| `0x80` | `ACK` | STM32 → Pi | Successful command acknowledgement. |
| `0x81` | `NACK` | STM32 → Pi | Rejected command or malformed request. |

Unused values are reserved.

---

## 6. Sequence Numbers

Every transmitted frame has a 32-bit `seq`. It increments monotonically per transmitter and wraps naturally from `0xFFFFFFFF` to `0`. It identifies that frame, not an individual measurement and not necessarily the request it answers. Solicited responses use payload-specific `response_to_seq` or `request_seq` for correlation. Sensor records have independent measurement timestamps.

The Raspberry Pi uses sequence numbers to detect duplicates, missing frames, stale responses, and request/response mismatches. A sequence number must not be reused for simultaneously outstanding transactions.

---

## 7. DATA_READY

`DATA_READY` is an STM32-to-Pi transport-availability signal using the **armed-then-assert model**:

```text
LOW   = no complete response frame is currently armed for DMA transmission
HIGH  = a complete response frame has been handed to DMA ownership and the DMA transfer is armed
```

**A frame merely staged in a software buffer but not yet DMA-armed is not sufficient.** Partial DMA activity is not sufficient. 

The STM32 may deassert `DATA_READY` after the frame is consumed. The signal does not identify the message type.

If a new snapshot replaces an unread response, the service increments a dropped/replaced counter and reports it through diagnostics.

**DATA_READY is the preferred low-latency notification mechanism when physically assigned; polling is retained for recovery, initially at 1 ms** (SD-17). A configurable 1 ms polling fallback rechecks staged-frame availability. When staged data is present while DATA_READY is low and no transfer is armed, the service re-arms the DMA transfer, reasserts DATA_READY, and reports poll-recovery and host-stall counters. **A 100 ms host-stall timeout aborts the active DMA transfer and returns the service to a re-armable state.** These software recovery paths have been exercised on the STM32 target, but the physical DATA_READY waveform and Pi-side GPIO path remain unvalidated.

---

## 8. Snapshot Coherency

A `SNAPSHOT` is a logically coherent view of the available STM32 state. For the intended six-joint stream, one snapshot contains all available joint records and associated CAN motor records.

**Snapshot coherency guarantee:** A snapshot is coherent when:
- every included record was copied completely;
- each record carries its own acquisition timestamp;
- the outer `frame_time_us` identifies assembly time only;
- record validity flags distinguish valid, stale, unavailable, and faulted data;
- sensor and motor record counts match the serialized payload;
- no record is modified during serialization or DMA.

Coherency does not imply simultaneous acquisition. TCA9548A channels are sampled sequentially. The timestamp spread across records must be available to the host.

**Fixed six-record snapshot:** Normal snapshots serialize six sensor records with stable logical IDs 0-5. Invalid records remain present with validity flags. Before all sensors are ready, serialize all six records with stable IDs and invalid/stale flags for unavailable channels; do not block the host indefinitely waiting for all channels.

**Replace-if-new semantics:** Snapshot publication uses replace-if-new:
- If no response frame is pending, serialize the newest caches into a free frame buffer and stage it for SPI.
- If a response frame is pending, serialize the newest caches into a free frame when available, then replace the pending frame; otherwise reuse the unread staged buffer.
- If both frame buffers are unavailable, retain producer caches, increment a dropped/replaced counter when the next frame supersedes an unread one, and never block acquisition.
- Increment a dropped/replaced snapshot counter when an unread snapshot is discarded; set a diagnostic flag in the next published snapshot/diagnostic message.

---

## 9. Measurement Timestamps

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

---

## 10. Time Domain

The Raspberry Pi is the system time authority. The STM32 maintains a monotonic local clock and does not reset that clock during synchronization.

```text
hub_time_us = local_time_us + time_offset_us
time_offset_us = pi_time_us - stm32_local_time_us
```

Exported sensor and motor timestamps use `hub_time_us`. The raw local monotonic clock remains an internal timing source. The transport timestamp `frame_time_us` must not replace measurement timestamps.

---

## 11. TIME_SYNC

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

---

## 12. Synchronization Validity and Monotonicity

The v1 synchronization validity timeout is **5 seconds**. When the timeout expires:

```text
local monotonic clock continues
hub-time calculation continues
time_sync_valid = false
```

The STM32 must not claim synchronized timestamps while `time_sync_valid` is false. Status/diagnostic messages must expose synchronization validity and, where useful, age since the last accepted update.

The first implementation may step the offset directly. If repeated updates cause undesirable timestamp discontinuities, a later contract revision may define filtered or slewed offset correction. The implementation must keep raw local time distinct from exported synchronized hub time.

---

## 13. Host Responsibilities

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

---

## 14. Error Handling

Reject a frame when magic, version, message type, length, CRC, sequence, or lifecycle permission is invalid. Return `NACK` with an error code such as:

- `INVALID_MAGIC`
- `UNSUPPORTED_VERSION`
- `INVALID_LENGTH`
- `CRC_ERROR`
- `INVALID_MESSAGE`
- `INVALID_STATE`
- `TIME_SYNC_INVALID`

A malformed or rejected frame must not modify application state. Recoverable transport faults may be retried or reported without changing lifecycle state; persistent DMA/NSS/transport faults follow the system lifecycle contract and may enter `ERROR`.

---

## 15. Lifecycle Integration

Normal sensor snapshots require the SPI service and sensor dependencies to be operational. `TIME_SYNC` may be accepted whenever the SPI transport is configured and able to receive valid commands, even if normal publication is not `ACTIVE`. Motor commands require CAN availability and must obey the lifecycle safety gate.

Lifecycle states and transition rules are canonical in `01_SYSTEM/SYSTEM_LIFECYCLE.md`.

---

## 16. Versioning and Integration Gates

Any incompatible change to field meaning/order, timestamp semantics, framing, CRC, or message semantics requires a protocol version increment.

**Remaining SPI integration gate is live-host and physical acceptance of the implemented transport:**

- maximum 5 MHz clock acceptance and associated DMA timing;
- NSS behavior and abort/recovery behavior under a real master;
- DATA_READY electrical timing and Raspberry Pi GPIO behavior;
- GPIO/SCK/MISO signal integrity;
- sustained and repeated 512-byte transactions;
- real Raspberry Pi ↔ STM32 request/response behavior and sequence/correlation handling.

**The current 5 MHz value is an integration ceiling, not hardware approval** (SD-01, SD-15).

The following are approved v1.0 decisions and must not be redefined by lower-level documents: Mode 0; fixed 512-byte frame; 490-byte maximum payload; CRC-32/ISO-HDLC parameters; pipelined request/response; five-second synchronization validity; one-way TIME_SYNC transaction-point estimate; direct offset stepping; fixed six-record sensor snapshots; replace-if-new behavior with drop diagnostics.

---

## 17. Contract Invariants

1. Raspberry Pi is the system time authority.
2. STM32 local time is monotonic and is never reset by synchronization.
3. Exported timestamps use local time plus the current accepted offset.
4. Measurement timestamps represent acquisition time, not transport time.
5. `frame_time_us` represents frame assembly time, not measurement time.
6. A snapshot is internally coherent (§8).
7. An SPI-owned DMA buffer cannot be modified during transmission.
8. CRC failure cannot modify application state.
9. Every frame has a sequence number.
10. `DATA_READY` is asserted only for a complete available frame whose DMA transfer is armed.
11. Loss of synchronization is explicitly reported through `time_sync_valid`.
12. Timestamp correlation uses the shared Pi time domain.

---

## Provenance

Reconciled from:
- `docs/project/protocols/spi-contract.md` (§§1–8, §10–14, §16–18; §9, §15 are component-internal)
- `docs/project/firmware/SNAPSHOT_COHERENCY_CONTRACT.md` (coherency guarantee, snapshot model, replace-if-new semantics)
- `docs/project/interfaces/spi-service-contract.md` (DATA_READY timing, host-stall timeout)
- `docs/project/interfaces/raspberry-pi-spi.md` (physical interface, hardware baseline)
