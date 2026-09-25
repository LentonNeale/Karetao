# TIME_SYNC Debug Mirror Instrumentation

> **As-built.** This document describes the current TIME_SYNC implementation (STM32-held offset, one-way TIME_SYNC). That design is superseded by [Issue #12](../../Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md) (2026-09-24) and will change when Issue #12 is implemented. Do not treat the mechanism described here as the target design.

## Overview

The STM32 firmware maintains a debug mirror of every `TimeService_SyncStateAccept` call, allowing hardware debuggers (SWD: Serial Wire Debug) to inspect the acceptance/rejection history without modifying the SPI protocol or firmware behavior.

## Motivation

During time synchronization development and debugging, it is valuable to observe:
- Which TIME_SYNC requests were accepted vs. rejected
- The computed offset and validation criteria applied
- Running counts of acceptance/rejection events

Rather than adding protocol extensions or firmware logging, the debug mirror stores this information in a volatile global variable accessible via SWD breakpoint inspection.

## Mirror Structure

```c
typedef struct
{
    uint64_t pi_time_us;           // Input: pi_time_us from TIME_SYNC request
    uint64_t local_capture_us;     // Input: local time captured by STM32
    int64_t  candidate_offset_us;  // Computed: candidate offset before acceptance
    uint32_t result;               // Output: TimeService_SyncResult code
    uint32_t accept_count;         // Counter: total accepted syncs
    uint32_t reject_count;         // Counter: total rejected syncs
} TimeService_SyncDebugMirror;
```

### Field Descriptions

| Field | Type | Purpose |
|-------|------|---------|
| `pi_time_us` | uint64_t | Pi's microsecond timestamp from the TIME_SYNC request |
| `local_capture_us` | uint64_t | STM32's local time at synchronization point |
| `candidate_offset_us` | int64_t | Computed offset (pi_time_us - local_time_us); positive = pi ahead, negative = local ahead |
| `result` | uint32_t | Result code: `TIME_SERVICE_SYNC_ACCEPTED` (0) or rejection reason |
| `accept_count` | uint32_t | Total count of accepted synchronization events (wraps at UINT32_MAX) |
| `reject_count` | uint32_t | Total count of rejected synchronization events (wraps at UINT32_MAX) |

## Global Declaration

The firmware declares the mirror as a global variable:

**Definition** (`Arm_Sensor_Hub/App/Src/time_service.c`):
```c
volatile TimeService_SyncDebugMirror g_time_sync_dbg = {0};
```

**Declaration** (`Arm_Sensor_Hub/App/Inc/time_service.h`):
```c
extern volatile TimeService_SyncDebugMirror g_time_sync_dbg;
```

The `volatile` keyword ensures the compiler does not optimize away reads/writes, and the debugger can inspect current values. The global scope (non-static) allows both firmware and host tests to access the same variable.

## Update Behavior

The mirror is updated on **every** call to `TimeService_SyncStateAccept`, regardless of the outcome:

1. **Input capture** (after offset calculation):
   - `pi_time_us` ← request pi_time_us
   - `local_capture_us` ← local_time_us
   - `candidate_offset_us` ← computed offset

2. **Result and counts** (before returning):
   - `result` ← the `TimeService_SyncResult` code being returned
   - `accept_count++` if result is `TIME_SERVICE_SYNC_ACCEPTED`
   - `reject_count++` if result is any rejection code

### Result Codes

- `TIME_SERVICE_SYNC_ACCEPTED` (0) — offset accepted and applied
- `TIME_SERVICE_SYNC_REJECTED_ARGUMENT` (1) — invalid inputs (NULL state, offset calculation overflow)
- `TIME_SERVICE_SYNC_REJECTED_SEQUENCE` (2) — non-monotonic sequence number
- `TIME_SERVICE_SYNC_REJECTED_OFFSET` (3) — offset outside acceptable limits (initial or step limits)

## SWD Readout Procedure

### Using OpenOCD (gdb)

1. **Start debug session** (with STM32CubeIDE or OpenOCD + arm-none-eabi-gdb)
2. **Set breakpoint** in the SPI TIME_SYNC handler or firmware main loop:
   ```gdb
   break SpiSlaveService_OnDataReceived
   continue
   ```

3. **Inspect the mirror** when breakpoint is hit:
   ```gdb
   print g_time_sync_dbg
   ```

   Example output:
   ```
   $1 = {
     pi_time_us = 1234567890,
     local_capture_us = 1234567800,
     candidate_offset_us = 90,
     result = 0,
     accept_count = 5,
     reject_count = 2
   }
   ```

4. **Watch for changes** between TIME_SYNC requests:
   ```gdb
   watch g_time_sync_dbg.result
   ```

### Using STM32CubeIDE

1. Open **Debug** perspective
2. Set breakpoint on `TimeService_SyncStateAccept` or any routine that calls it
3. When paused, open the **Variables** view
4. Search for `g_time_sync_dbg` in the Locals panel
5. Expand to see all fields and their current values

### Hardware Watchpoint (for real-time monitoring)

Some debuggers support hardware data watchpoints on specific memory addresses:

```gdb
# Set hardware watchpoint on the entire struct
watch *((TimeService_SyncDebugMirror*)&g_time_sync_dbg)
```

This halts execution whenever the mirror is written, showing the exact instruction performing the update.

## Testing

The host test suite (`protocol_test_main.c`) includes assertions on the mirror:

- **`TestInitialAcceptanceAndRuntimeRejection()`** — verifies ACCEPTED and REJECTED_OFFSET paths
- **`TestTimeoutResetAndRecovery()`** — verifies mirror updates across recovery scenarios
- **`TestSyncDebugMirrorRejectionCodes()`** — verifies REJECTED_ARGUMENT and REJECTED_SEQUENCE paths

Run tests with:
```bash
ctest --preset HostTests
```

## Firmware Build

The mirror is compiled **only in firmware builds** (not in host tests). Host tests use a stub:

```c
volatile TimeService_SyncDebugMirror g_time_sync_dbg = {0};
```

This allows tests to verify mirror logic without introducing test dependencies into the firmware.

The mirror is guarded by:
```c
#ifndef TIME_SERVICE_HOST_TEST
    g_time_sync_dbg.result = ...;
    g_time_sync_dbg.accept_count++;
#endif
```

Verify the mirror compiles:
```bash
cmake --build --preset Debug
```

## Performance Notes

- **Zero runtime overhead in production builds** if debugger is not attached
- **Minimal memory overhead**: 56 bytes per mirror instance
- **No SPI protocol changes** — mirror is internal to firmware only
- **No SRAM fragmentation** — mirror is static and pre-allocated

## Troubleshooting

### Mirror values appear stale

- Ensure the `volatile` keyword is present in the declaration
- Confirm the debugger is attached via SWD
- Check that firmware was built with optimizations disabled (`-O0` or `-Og`)

### Breakpoint not hit in `TimeService_SyncStateAccept`

- TIME_SYNC messages may be rare; set a looser breakpoint in the SPI handler
- Use a hardware watchpoint on `g_time_sync_dbg.result` instead
- Add a `DebugBreak()` or `while(1)` temporarily in the function to force a halt

### Mirror always shows zeros

- Verify the firmware was compiled without `TIME_SERVICE_HOST_TEST` defined
- Check that the hardware is powered and SWD connection is active
- Ensure no compiler optimizations removed the variable

## SPI Transaction Timing Mirror

### Overview

In addition to TIME_SYNC acceptance tracking, the firmware captures pipeline timing information at four critical points in the SPI transaction lifecycle. This timing mirror reveals latencies between:
- DMA completion (when the host clocks out the request)
- Request processing start (when the task begins handling the request)
- Response frame staging (when the reply is prepared and buffered)
- DATA_READY assertion (when the GPIO signals frame readiness to the host)

This data is essential for characterizing the pipeline delay between a TIME_SYNC request receipt and the STM32's local time capture.

### Mirror Structure

```c
typedef struct
{
    uint32_t dma_complete_raw;     // Raw TIM2 counter at ISR (DMA complete)
    uint32_t process_start_us;     // TimeService_NowUs() at SpiSlaveService_Process() entry
    uint32_t response_staged_us;   // TimeService_NowUs() when response is staged
    uint32_t data_ready_set_us;    // TimeService_NowUs() when DATA_READY GPIO is asserted
    uint8_t  request_type;         // Message type of last processed request
    uint32_t request_seq;          // Sequence number of last processed request
} SpiSlaveService_TimingMirror;
```

### Field Descriptions

| Field | Type | Purpose |
|-------|------|---------|
| `dma_complete_raw` | uint32_t | Raw TIM2 counter value captured in the DMA completion ISR; measures wall-clock time at frame reception |
| `process_start_us` | uint32_t | Microsecond timestamp at `SpiSlaveService_Process()` entry when request is pending; reveals scheduling delay |
| `response_staged_us` | uint32_t | Microsecond timestamp when response frame is prepared and staged in the frame pool |
| `data_ready_set_us` | uint32_t | Microsecond timestamp when `DATA_READY` GPIO is asserted to signal the host that a response is ready |
| `request_type` | uint8_t | SPI message type (e.g., `SPI_MESSAGE_TIME_SYNC`) of the last processed request |
| `request_seq` | uint32_t | Sequence number from the last processed request; correlates this timing sample to the request |

### Timing Intervals

The four timestamps enable calculation of three key intervals:

1. **DMA-to-Process delay**: `process_start_us - dma_complete_raw` (usually ~1–10 ms, accounts for ISR and task scheduling)
2. **Process-to-Stage delay**: `response_staged_us - process_start_us` (request validation and response serialization)
3. **Stage-to-Ready delay**: `data_ready_set_us - response_staged_us` (frame pool management and GPIO assertion)

For TIME_SYNC requests specifically, `process_start_us` directly correlates to the STM32's local time capture point, since `TimeService_AcceptSync()` is called early in request processing.

### Global Declaration

**Definition** (`Arm_Sensor_Hub/App/Src/spi_slave_service.c`):
```c
volatile SpiSlaveService_TimingMirror g_spi_timing_dbg = {0};
```

**Declaration** (`Arm_Sensor_Hub/App/Inc/spi_slave_service.h`):
```c
extern volatile SpiSlaveService_TimingMirror g_spi_timing_dbg;
```

### Capture Points

The mirror is updated at four points in the transaction lifecycle:

1. **DMA Completion (ISR context)** — `HAL_SPI_TxRxCpltCallback()`:
   - Captures `dma_complete_raw = TimeService_RawCounter()` (raw TIM2 value, not microseconds)

2. **Request Processing Start** — `SpiSlaveService_Process()`:
   - Captures `process_start_us = TimeService_NowUs()` when `s_request_pending` is true

3. **Response Frame Staged** — `SpiSlaveService_StageResponseFrame()`:
   - Captures `response_staged_us = TimeService_NowUs()` when frame is successfully staged

4. **DATA_READY GPIO Asserted** — `SpiSlaveService_SetDataReadyPin(true)`:
   - Captures `data_ready_set_us = TimeService_NowUs()`
   - Also stores `request_type` and `request_seq` from the last processed request

### Timing Correlation with TIME_SYNC

For TIME_SYNC requests, the timing mirror reveals the critical path:

```
Host sends TIME_SYNC
      ↓
SPI DMA completes (time = dma_complete_raw)
      ↓
ISR sets s_request_pending flag
      ↓
Task scheduling delay (~1–10 ms typical)
      ↓
Process() called: process_start_us = TimeService_NowUs()
      [← This is the de-facto capture time for TIME_SYNC]
      ↓
ProcessRequestFrame() → TimeService_AcceptSync() captures offset
      ↓
Response is staged: response_staged_us
      ↓
DATA_READY asserted: data_ready_set_us
      ↓
Host detects DATA_READY and begins reading response
```

The key insight: **`process_start_us` is the relevant timestamp for TIME_SYNC synchronization**, not `dma_complete_raw`. The `dma_complete_raw` indicates when the physical transaction arrived, while `process_start_us` is when the firmware time service actually captured the local timestamp.

### SWD Readout Procedure

Use the same procedure as for the TIME_SYNC mirror:

```gdb
print g_spi_timing_dbg
```

Example output:
```
$1 = {
  dma_complete_raw = 0xABCD1234,
  process_start_us = 1000500,
  response_staged_us = 1000550,
  data_ready_set_us = 1000600,
  request_type = 5,
  request_seq = 42
}
```

### Testing

The host test suite (`service_test_main.c`) includes assertions on the timing mirror:

- **`TestSpiSlaveServiceRequestHandling()`** (TIME_SYNC path) — verifies:
  - All four timestamps are non-zero after a successful transaction
  - Timestamps are in expected order: `dma_complete_raw < process_start_us < response_staged_us < data_ready_set_us`
  - `request_type` and `request_seq` match the last processed request

Run tests with:
```bash
ctest --preset HostTests
```

## SWD Readout and Data Correlation

The debug mirror structures (`TimeService_SyncDebugMirror` and `SpiSlaveService_TimingMirror`) are designed for inspection via SWD (Serial Wire Debug) using OpenOCD and GDB.

### Readout Procedure

See [SWD_READOUT_PROCEDURES.md](SWD_READOUT_PROCEDURES.md) for:
1. Extracting TimeService_SyncDebugMirror (offset and validation state)
2. Extracting SpiSlaveService_TimingMirror (transaction milestones)
3. Verifying TIM2 prescaler and clock frequency
4. Correlating Pi probe measurements with STM32 actual values

### Post-Measurement Analysis

After running spi_time_sync_probe.py on the Pi and reading STM32 debug mirrors via SWD:

1. **Offset validation:** Compare probe-estimated offsets with SWD-readout actual values
2. **Transaction timing:** Validate that measured transaction latencies match contract (SPI_SYSTEM_INTERFACE.md §4)
3. **Drift detection:** Check that offset doesn't creep beyond ±1ms/sync (SYS-SYNC-001)

See [TIME_SYNC_VALIDATION.md](../../Documentation/05_VERIFICATION/TIME_SYNC_VALIDATION.md) for acceptance criteria.

## References

- Time Service Contract: `TIME_SERVICE_SYNC_INSTRUMENTATION.md` (this document)
- Time Service Implementation: `Arm_Sensor_Hub/App/Src/time_service.c`
- Time Service Interface: `Arm_Sensor_Hub/App/Inc/time_service.h`
- SPI Protocol: `Arm_Sensor_Hub/Documentation/development.md`
- SWD Readout Guide: [SWD_READOUT_PROCEDURES.md](SWD_READOUT_PROCEDURES.md)
