# CAN Service Contract

**Status:** Pre-freeze approval baseline  
**Owner:** `CanService`  
**Boundary:** Application callers -> CAN service -> MKS C API -> STM32 bxCAN HAL

## Purpose

Provide deterministic CAN transport and MKS motor access for the STM32 application. The service owns CAN peripheral readiness, frame transmission/reception, motor registration, polling, and transport diagnostics.

The MKS library owns command encoding, checksum validation, and response decoding. It does not own HAL handles, queues, retries, timing, or bus recovery.

## Public Interface

Header: `App/Inc/can_service.h`

- `CanService_Init()` configures filters, starts CAN, and initializes service state.
- `CanService_Activate()` permits normal CAN processing and transmission.
- `CanService_Process()` drains RX FIFO and runs the poll scheduler.
- `CanService_RegisterMotor()` binds a logical joint/motor index, mapping configuration version, Servo42/Servo57 selection, and 11-bit CAN ID.
- Command functions encode through `mks_api.h` and transmit through the service.
- Response accessors return the latest decoded response and counters. `CanService_GetLatestMotorValues()` exposes the CAN-owned bounded latest-value cache for Snapshot Builder to copy.

## Lifecycle and Safety

The service follows [LIFECYCLE_CONTRACT.md](LIFECYCLE_CONTRACT.md):

- `UNCONFIGURED`: no valid CAN configuration is available.
- `INACTIVE`: CAN is configured but normal traffic is disabled.
- `ACTIVE`: normal TX, RX processing, and polling are permitted.
- `ERROR`: transport cannot safely continue.

Normal motor commands are permitted only while CAN is `ACTIVE`. The current implementation enforces this centrally in `CanService_TransmitFrame()`.

Emergency-stop behavior is currently fail-closed with the same gate as other commands. A future safety review may authorize emergency stop while `ERROR` only when the HAL transport is demonstrably operational; that exception must not be assumed by callers.

## Configuration Contract

- CAN uses standard 11-bit identifiers.
- `CAN_BIT_TIMING_EVIDENCE.md` records the current 875 kbps generated configuration and a calculated 1 Mbps candidate for the 42 MHz APB1 clock. The candidate is not applied or approved until controller and physical-layer validation is complete.
- Motor registration rejects IDs above `0x7FF`.
- Motor indices are fixed-size and range from `0` to `CAN_SERVICE_MAX_MKS_MOTORS - 1`.
- The current registry capacity is eight motors.
- The current filter accepts all CAN IDs into FIFO0; service-level motor registration determines which frames are decoded.
- A registered motor owns its configured default CAN ID for response association. Duplicate IDs are not currently rejected and must be rejected before production use.

## Current Transport Behavior

### TX

`CanTx_Queue` is the bounded logical owner for safety, motion, and poll frames. It is priority ordered (`SAFETY`, `MOTION`, then `POLL`) and FIFO within a priority. Runtime HAL queue draining is deferred until bxCAN recovery behavior is validated.

- Frames are encoded into a fixed `MksCanFrame`.
- Command and poll APIs enqueue into one eight-entry logical queue; `CanService_Process()` is the only normal HAL transmitter and drains at most one entry per pass.
- HAL failure retries the dequeued entry at most three times before incrementing the retry-exhausted diagnostic.
- Queue-full rejection increments the queue-drop diagnostic.
- TX payloads are copied into a local fixed-size eight-byte buffer for the HAL call.

### RX

- `CanService_Process()` drains FIFO0 until empty.
- Standard frames with DLC greater than eight are discarded.
- Frames from unregistered CAN IDs are ignored.
- Registered frames are passed to `mks_decode()`.
- Successful responses replace the per-motor last-response record.
- Decode failures increment the per-motor decode-error counter.
- Successful decodes update the motor latest-value record with generic decoded feedback payload, acquisition timestamp, synchronization quality, freshness, and diagnostics counters. A decode failure marks that record stale without overwriting its last valid feedback payload.
- RX overflow counters and overflow recovery are not yet implemented.

### Polling

- Default polling period is 20 ms.
- Registered motors are selected round-robin.
- Each selected motor alternates encoder-value and realtime-speed requests.
- `CanService_SetPollPeriodMs(0)` disables automatic polling.
- Manual commands and polling currently share the immediate HAL mailbox path; ordering is not guaranteed if callers invoke them concurrently.

## Required Production Decisions

Before production use, decide and document:

1. Retry delay and controller-specific timeout semantics.
2. RX FIFO overflow detection and reporting.
3. Duplicate CAN-ID registration behavior.
4. Per-motor polling period and response timeout.
5. Exact HAL error to service-status mapping.
6. Whether emergency stop is allowed during `ERROR`.
7. CAN bitrate, sample point, and retransmission settings derived from the actual APB1 CAN clock.
8. Transceiver, termination, topology, cable/stub length, and controller-specific traffic evidence required to validate the calculated bitrate/load target.

## Bus-Off Policy

`CanService_Process()` checks `HAL_CAN_ERROR_BOF` in task context, stops CAN, inhibits normal queue draining, and schedules recovery with escalating 100 ms to 1 s delay. Three events in a 60 s rolling window enter lifecycle `ERROR`. A successful HAL restart transitions `ERROR` to `INACTIVE`; it does not resume normal queue draining or motion. `CanService_Activate()` is the only path that clears the inhibit after recovery. HAL error-code behavior, stop/start timing, controller/transceiver recovery, and timeout evidence remain integration gates.

## Diagnostics

Minimum required diagnostics:

- lifecycle state and last fault code;
- per-motor RX decode successes and failures;
- TX successes, HAL failures, and queue-full failures once a queue exists;
- RX FIFO overflow count;
- bus-off count and last recovery result;
- poll requests sent and poll responses received;
- last response timestamp and sequence/command code.

Counters are task-owned. ISR callbacks, if added later, shall record minimal flags/counters and defer lifecycle mutation and recovery to task context.

Diagnostic and response timestamps use the shared 64-bit monotonic time extension derived from TIM2. They must not use independent `HAL_GetTick()` or raw 32-bit timer values.

## Latest-Value Cache Ownership

CanService owns one fixed `Motor_LatestValue` slot for each motor index. A slot carries logical joint and motor identity, CAN ID, generic decoded feedback code/payload, optional controller status, validity flags, acquisition timestamp, synchronization quality, calibration/configuration versions, freshness, and RX success/decode-error counters. The cache uses generic MKS decoded fields because exact controller feedback semantics remain uncommissioned.

Snapshot Builder may read the array through `CanService_GetLatestMotorValues()` and copy it into a separate serialization buffer. It must not mutate the cache or write into an SPI frame buffer. CAN processing is the only writer.

## Timing and Concurrency

- `CanService_Process()` runs from task context.
- Lifecycle mutation, recovery, and queue management run from task/system context only.
- No service API may be called from an ISR unless explicitly marked ISR-safe in a future revision.
- Normal processing must be bounded; a future RX drain limit may be required to prevent starvation of other tasks.
- If multiple tasks can issue commands, a mutex or single command-owner task is required before concurrent use is supported.

## Verification

- Invalid motor index, model, and CAN ID are rejected.
- TX is rejected while CAN is not `ACTIVE`.
- Registered valid frames decode and update the correct motor record.
- Unknown IDs do not modify motor state.
- Malformed frames increment diagnostics and do not modify the last valid response.
- Poll scheduling is disabled at period zero and round-robin when enabled.
- Bus-off and queue behavior require hardware or mocked-HAL tests once implemented.
