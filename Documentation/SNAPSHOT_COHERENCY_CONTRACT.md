# Snapshot Coherency and Buffer Ownership Contract

**Status:** Pre-freeze approval baseline  
**Owner:** SensorTask, CAN data collection, Snapshot Builder, and SpiSlaveService  
**Boundary:** Sensor/CAN producers -> coherent SPI snapshot

## Purpose

Define how sensor and motor observations become one SPI `SNAPSHOT` without exposing partially updated data or modifying a buffer owned by DMA.

## Target Data Set

- Six logical sensor axes map to TCA9548A channels 0-5 by default.
- A normal snapshot always serializes six sensor records; `sensor_count` is the serialized record count, not the valid-record count.
- Sensor IDs 0-5 identify logical axes; physical mux channels remain configuration details.
- Each sensor record carries identity, validity flags, acquisition timestamp, and values.
- Motor records are associated by logical motor index and CAN ID. The final joint-to-motor mapping remains a commissioning decision.
- The current firmware implements only channel 0 and one configured motor; this contract describes the target model.

## Ownership Model

Do not let SensorTask and CAN service write to one shared snapshot build buffer. Each producer owns a latest-value cache. A Snapshot Builder copies those caches into one of two statically allocated serialized SPI frame buffers:

```text
SensorTask -> sensor latest-value cache ----┐
                                           ├-> Snapshot Builder -> free SPI frame buffer -> DMA
CAN service -> motor latest-value cache ----┘
```

Rules:

1. SensorTask owns sensor records and CAN service owns motor records.
2. Producers never write an SPI frame buffer.
3. Snapshot Builder reads stable producer caches and writes only a free frame buffer.
4. The SPI service owns a staged frame until the transaction ends.
5. DMA callbacks only mark completion/error and defer processing to task context.
6. A DMA-owned buffer cannot be replaced or overwritten.
7. A published frame is immutable until SPI releases it.

`SnapshotFrame_Pool` provides two static 512-byte buffers with `FREE`, `STAGED`, and `DMA_ACTIVE` ownership states. `SnapshotBuilder_Stage()` invokes serialization only for a free buffer, or replaces an unread staged buffer when no free buffer exists. It never supplies a DMA-active buffer to the serializer. `SnapshotFramePool_BeginDma()` transitions `STAGED` to `DMA_ACTIVE`; `SnapshotFramePool_CompleteDma()` releases the active buffer to `FREE`.

The synchronization mechanism must be static and bounded. In v1, Snapshot Builder and SPI ownership transitions execute in one task context; DMA callbacks only defer completion to that context. Do not hold a mutex across SPI DMA.

## Publish Policy

Initial policy: **replace-if-new**.

- If no response frame is pending, serialize the newest caches into a free frame buffer and stage it for SPI.
- If a response frame is pending, serialize the newest caches into a free frame when available, then replace the pending frame; otherwise reuse the unread staged buffer.
- If both frame buffers are unavailable, retain producer caches, increment a dropped/replaced counter when the next frame supersedes an unread one, and never block acquisition.
- Increment a dropped/replaced snapshot counter when an unread snapshot is discarded.
- Set a diagnostic flag in the next published snapshot/diagnostic message.
- Never block sensor acquisition waiting for the Raspberry Pi.

A bounded queue may replace this policy in a future revision if measured data loss requires it.

## Coherency Definition

A snapshot is coherent when:

- every included record was copied completely;
- each record carries its own acquisition timestamp;
- the outer `frame_time_us` identifies assembly time only;
- record validity flags distinguish valid, stale, unavailable, and faulted data;
- sensor and motor record counts match the serialized payload;
- no record is modified during serialization or DMA.

Coherency does not imply simultaneous acquisition. TCA9548A channels are sampled sequentially. The timestamp spread across records must be available to the host.

## Startup and Partial Availability

Before all sensors are ready, the STM32 may publish a snapshot only if the payload contract permits partial snapshots. Unavailable records must be present with stable identity, invalid/stale flags, zeroed values where required, and a diagnostic reason.

The v1 target is a fixed six-record snapshot. Before all sensors are ready, serialize all six records with stable IDs and invalid/stale flags for unavailable channels. Do not block the host indefinitely waiting for all channels.

## Sensor and Motor Coordination

- SensorTask owns sensor acquisition records.
- CAN service owns motor response records.
- SpiSlaveService owns serialization and transmit-buffer ownership.
- No service may write directly into the SPI DMA-owned buffer.
- The application coordinator determines when a snapshot is publishable; the SPI service determines when it is transferable.

## Timing and Freshness

- Sensor timestamps are captured immediately after successful AS5600 measurement bytes are received and decoded.
- Sensor timestamps represent acquisition time in the synchronized hub time domain when valid.
- Unsynchronized timestamps must be marked with a validity flag.
- The host may use record timestamp age relative to `frame_time_us` to determine freshness.
- The shared time service must provide a 64-bit extension of the 32-bit, 1 MHz TIM2 counter before freshness logic is implemented.

## Required Diagnostics

- published snapshot sequence;
- replaced/dropped snapshot count;
- current producer-cache and frame-buffer ownership;
- last publish time;
- last SPI consume time;
- DMA busy/error state;
- count of partial or invalid records.

## Verification

- Producer writes never overlap the SPI-owned buffer.
- A snapshot swap is atomic from the consumer’s perspective.
- CRC and payload length cover exactly the serialized snapshot.
- Simulated host stalls increment the dropped counter without blocking acquisition.
- A partial sensor set is represented without stale valid flags.
- DMA completion releases the front buffer only after the transaction boundary is safe.
