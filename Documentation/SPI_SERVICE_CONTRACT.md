# SPI Slave Service Contract

**Status:** Pre-freeze approval baseline  
**Owner:** `SpiSlaveService`  
**Boundary:** Application payload producer -> SPI3 HAL/DMA -> Raspberry Pi

## Purpose

Move validated application frames between the STM32 and Raspberry Pi while preserving buffer ownership, DATA_READY semantics, lifecycle safety, and bounded RTOS behavior.

The wire format and message meanings are defined in [SPI_CONTRACT.md](SPI_CONTRACT.md). Payload layouts are defined in [SPI_PAYLOAD_SCHEMA.md](SPI_PAYLOAD_SCHEMA.md). Snapshot ownership is defined in [SNAPSHOT_COHERENCY_CONTRACT.md](SNAPSHOT_COHERENCY_CONTRACT.md).

## Current Status

`App/Src/spi_slave_service.c` owns two static serialized-frame buffers through `SnapshotFrame_Pool`, stages fixed-frame responses selected by `SpiProtocol_ProcessRequest()`, and is the sole production owner of the `DATA_READY` GPIO. It does not yet start hardware DMA, receive hardware requests, or perform final snapshot serialization. This contract defines the implementation target and must not be read as proof that those behaviors already exist.

## Lifecycle

- `UNCONFIGURED`: SPI service resources and buffers are unavailable.
- `INACTIVE`: resources are prepared but publication and DATA_READY are disabled.
- `ACTIVE`: validated frames may be published and host transactions may be serviced.
- `ERROR`: DMA, NSS, framing, or persistent transport failure requires recovery.

SPI activation does not activate sensors or CAN. Normal snapshots require those dependencies to provide valid/invalid records according to the payload contract. `TIME_SYNC` may be accepted whenever RX transport is configured and operational.

Normal snapshots serialize six sensor records with stable logical IDs 0-5. Invalid records remain present with validity flags. The outer frame is limited to 512 bytes with a maximum 490-byte payload. `frame_time_us` is frame assembly time; record timestamps are acquisition timestamps.

## Buffer Ownership

Use producer-owned latest-value caches and two static serialized SPI frame buffers:

```text
SensorTask -> sensor cache ----┐
                               ├-> Snapshot Builder -> free frame buffer -> DMA_TX -> FREE
CAN service -> motor cache ----┘
```

- SensorTask owns sensor records; CAN service owns motor records.
- Snapshot Builder owns serialization into a free frame buffer.
- SPI service owns staged and `DMA_TX` buffers.
- DMA owns the memory for the duration of the transfer.
- DMA callbacks do not serialize, parse, or perform lifecycle transitions.
- Ownership changes occur in task context or a bounded critical section.
- No buffer is modified while DMA owns it.

The snapshot mechanism is the producer-cache/Snapshot-Builder/two-frame-buffer policy in [SNAPSHOT_COHERENCY_CONTRACT.md](SNAPSHOT_COHERENCY_CONTRACT.md). If both frame buffers are unavailable, acquisition is not blocked; the newest replacement/drop is counted.

`SpiSlaveService_StageSnapshot()` accepts a bounded serializer callback in task context and stages its output. `SpiSlaveService_BeginDmaTransfer()` exposes an immutable staged frame and marks it DMA-active; `SpiSlaveService_CompleteDmaTransfer()` releases it after deferred completion. Hardware DMA invocation remains future work.

## RX/TX and NSS

The Raspberry Pi is SPI master and generates all clocks. The service uses pipelined request/response transactions: transaction N clocks a response staged before N while carrying request N; the STM32 validates request N and stages response N+1 between transactions. The first boot response is a defined status, ACK, or NACK frame.

A partial or aborted NSS transaction must:

- release the active buffer safely;
- record a transport diagnostic;
- avoid publishing a partial application message;
- re-arm the RX/TX path from task context;
- preserve the last valid response/snapshot.

DMA mode details must support the fixed frame limit; maximum SPI clock remains the designated Raspberry Pi integration gate. The transaction model itself is frozen as pipelined request/response.

## Protocol State

`SpiProtocol_ProcessRequest()` validates the fixed 512-byte request frame, magic, version, little-endian payload length, CRC over header plus payload, request sequence, and supported message type. It returns a fixed-frame NACK without accepting invalid input. `GET_SNAPSHOT` consumes a queued unsolicited snapshot as a correlated `SNAPSHOT` response and writes `response_to_seq`; this takes priority over unsolicited publication. `GET_STATUS` receives an ACK. `TIME_SYNC` receives payload validation in the protocol layer and is applied in task context through `TimeService_AcceptSync()` before the staged ACK/NACK reply is published. The boot response is a fixed status frame.

## DATA_READY

- Assert only when a complete valid frame is staged and SPI is `ACTIVE`; it does not indicate sensor cache changes.
- Do not assert for a buffer still being serialized or for a partial DMA transfer.
- Deassert when the staged buffer transfers to DMA ownership.
- Force low during `INACTIVE`, `ERROR`, and shutdown.
- Poll staged-frame availability every configurable 1 ms by default. A poll that finds staged data while DATA_READY is low reasserts it and increments `poll_recovery_count`.
- Count rising notifications in `notification_count`; count a still-staged frame once after the configured host-stall interval in `host_stall_count`.

SensorTask does not drive DATA_READY in production.

## Hardware Validation Procedure

Before approving the initial 5 MHz maximum, measure on the assembled STM32/Raspberry Pi path: DATA_READY rising edge only after a complete 512-byte frame is staged; Pi detection latency and missed-edge recovery through the 1 ms poll; NSS-to-DMA start and DMA completion timing; frame CRC/sequence correctness under continuous traffic and host stalls; GPIO/SCK/MISO signal integrity; and replacement/drop/host-stall diagnostics. Record the Pi driver settings, cable/topology, clock rate, logic-analyzer traces, error counts, and pass/fail limits. The 5 MHz maximum remains an integration gate until this evidence is accepted.

## DMA and Deferred Processing

DMA completion/error callbacks must remain minimal:

- capture completion/error status;
- set a task notification or static flag;
- request a context switch only when required;
- defer buffer release, parsing, lifecycle changes, and diagnostics aggregation to `SpiSlaveService_Process()`.

No blocking, serialization, CRC calculation, or application command execution may occur in an ISR.

## Validation and Errors

The service validates magic, version, message type, payload length, CRC, sequence, and lifecycle permission before applying a host command. Invalid requests return a NACK when a response transaction is available and never modify application state.

Fault classes:

- transient NSS/DMA issue: re-arm locally and remain `ACTIVE` if safe;
- repeated DMA/transport issue: enter lifecycle `ERROR` and stop DATA_READY;
- invalid application command: return NACK without changing lifecycle state;
- shutdown: stop new transfers, force DATA_READY low, preserve diagnostics.

## Timing and Concurrency

- `SpiSlaveService_Process()` runs from task context.
- No public SPI service mutation API is ISR-safe unless explicitly documented later.
- Do not hold a mutex across DMA or host clocking.
- Serialization must be bounded or performed into a preallocated buffer outside time-critical paths.
- Maximum frame size is 512 bytes, with a maximum payload of 490 bytes. DMA transfer budget follows this fixed frame limit. Maximum SPI clock remains the designated Raspberry Pi integration gate.
- CRC is CRC-32/ISO-HDLC: polynomial `0x04C11DB7`, initial `0xFFFFFFFF`, reflected input/output, final XOR `0xFFFFFFFF`, little-endian wire field, covering header plus payload and excluding CRC.
- Synchronization validity expires after 5 seconds without an accepted TIME_SYNC update.
- All frame and measurement timestamps use the shared 64-bit extension of the 32-bit, 1 MHz TIM2 counter.

## Required Diagnostics

- lifecycle state and last fault;
- DMA starts/completions/errors;
- aborted NSS transactions;
- CRC/version/length rejection counts;
- DATA_READY assertions/deassertions;
- dropped/replaced frame count;
- last transmitted sequence;
- time synchronization validity and last accepted sync sequence.

## Verification

- DATA_READY never asserts for incomplete data.
- TX buffers remain unchanged while DMA is active.
- Host stalls do not block sensor acquisition.
- Aborted transactions re-arm safely.
- Invalid frames produce no application side effects.
- Lifecycle deactivation forces DATA_READY low and prevents new publication.
- Buffer ownership transitions are observable in diagnostics and cannot produce double release.
