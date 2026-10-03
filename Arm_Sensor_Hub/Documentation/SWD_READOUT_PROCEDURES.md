# SWD Readout Procedures for TIME_SYNC Instrumentation

> **As-built.** This document describes the current TIME_SYNC implementation (STM32-held offset, one-way TIME_SYNC). That design is superseded by [Issue #12](../../Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md) (2026-09-24) and will change when Issue #12 is implemented. Do not treat the mechanism described here as the target design.

## Overview

This document describes how to extract timing and synchronization data from the STM32F405RGT6 via SWD (Serial Wire Debug) using OpenOCD and gdbserver. These procedures are necessary to correlate Pi-side probe measurements with actual STM32 local clock values and transaction timings.

## Prerequisites

- ST-Link V2 or compatible SWD debugger
- OpenOCD installed: `apt install openocd` (on Raspberry Pi or build machine)
- arm-none-eabi-gdb or similar GDB variant
- Karetao firmware built with DEBUG=1 (includes symbol table)

## Quick Start

### Setup OpenOCD Server (in one terminal)

```bash
openocd -f interface/stlink-v2.cfg -f target/stm32f4x.cfg \
  -c "init" -c "targets" -c "halt" \
  -c "gdb_breakpoint_override hard"
```

Expected output:
```
Open On-Chip Debugger 0.11.0
...
target state: halted
target halted due to breakpoint...
```

### Connect GDB in Another Terminal

```bash
arm-none-eabi-gdb build/firmware.elf
(gdb) target remote localhost:3333
(gdb) monitor reset halt
(gdb) info locals
(gdb) info threads
(gdb) bt  # backtrace to see current function
```

## Procedure 1: Read TimeService_SyncDebugMirror

**Purpose:** Extract the last accepted TIME_SYNC offset and validation state

**Global Variable Location:**
- File: `Arm_Sensor_Hub/App/Src/time_service.c`
- Symbol: `g_time_sync_dbg` (TimeService_SyncDebugMirror struct)
- Address: Determined by linker (use OpenOCD `monitor symbols | grep g_time_sync_dbg`)

**Steps in GDB:**

```gdb
(gdb) monitor reset halt                    # Stop firmware
(gdb) print /x &g_time_sync_dbg             # Get address (e.g., 0x20001234)
(gdb) x /16x 0x20001234                    # Dump 16 bytes (struct size)
```

**Interpret the Output:**

TimeService_SyncDebugMirror struct layout (from time_service.h):
```c
struct {
    uint64_t pi_time_us;         // Offset 0, 8 bytes — Pi time at ACK
    uint64_t local_capture_us;   // Offset 8, 8 bytes — STM32 local time at capture
    int64_t candidate_offset_us; // Offset 16, 8 bytes — pi_time_us - local_capture_us
    uint32_t result;             // Offset 24, 4 bytes — result code (0=OK, others=error)
    uint32_t accept_count;       // Offset 28, 4 bytes — acceptance count
    uint32_t reject_count;       // Offset 32, 4 bytes — rejection count
}
```

Example:
```gdb
(gdb) x /16x 0x20001234
0x20001234: 0x000f4240  0x00000000  0x0007d0ff  0x00000000
0x20001244: 0x000f4240  0x00000000  0x00000000  0x00000000
0x20001254: 0x00000000  0x00000005  0x00000003
```

**Decode (little-endian):**
- pi_time_us = 0x0000000000000f4240 = 1000000 µs
- local_capture_us = 0x0000000000000f4240 = 1000000 µs  
- candidate_offset_us = 0x0000000000000000 = 0 µs (local and pi clocks aligned at this moment)
- result = 0x00000000 = OK
- accept_count = 5
- reject_count = 3

**Validation:**
- ✓ result == 0: Offset is valid
- ✓ accept_count > 0: At least one sync succeeded
- ✓ |candidate_offset_us| < 2000000: Offset within ±2s (sanity check)

## Procedure 2: Read SpiSlaveService_TimingMirror

**Purpose:** Extract the timing of the last SPI transaction (DMA completion, response staging, DATA_READY)

**Global Variable Location:**
- File: `Arm_Sensor_Hub/App/Src/spi_slave_service.c`
- Symbol: `g_spi_timing_dbg` (SpiSlaveService_TimingMirror struct)
- Address: Determined by linker

**Steps in GDB:**

```gdb
(gdb) print &g_spi_timing_dbg
(gdb) print g_spi_timing_dbg
```

**Struct Layout (from spi_slave_service.h):**
```c
struct {
    uint32_t dma_complete_raw;  // Offset 0, 4 bytes — raw TIM2 counter at DMA ISR
    uint32_t process_start_us;  // Offset 4, 4 bytes — TimeService_NowUs() at process entry
    uint32_t response_staged_us; // Offset 8, 4 bytes — TimeService_NowUs() at response stage
    uint32_t data_ready_set_us;  // Offset 12, 4 bytes — TimeService_NowUs() at DATA_READY assert
    uint16_t request_type;       // Offset 16, 2 bytes — message type (0x12 = TIME_SYNC)
    uint16_t request_seq;        // Offset 18, 2 bytes — sequence number
}
```

Example GDB output:
```gdb
(gdb) print g_spi_timing_dbg
$1 = {
  dma_complete_raw = 0x123456,
  process_start_us = 0x1000100,
  response_staged_us = 0x1000200,
  data_ready_set_us = 0x1000300,
  request_type = 0x12,
  request_seq = 0x0042
}
```

**Interpretation:**
- dma_complete_raw: 0x123456 ticks at 1 MHz = 1193046 µs
- Delays between milestones:
  - DMA to process start: 1000100 - (0x123456 µs) = small delay (ISR overhead + task switch)
  - Process start to response staged: 1000200 - 1000100 = 100 µs (frame building)
  - Response staged to DATA_READY: 1000300 - 1000200 = 100 µs (GPIO propagation + ISR entry)

## Procedure 3: Verify TIM2 Clock Configuration

**Purpose:** Confirm prescaler is 83 and clock is running at ~1 MHz

**Steps in GDB:**

```gdb
(gdb) monitor reset halt
(gdb) print /t (TIM2->PSC)    # Prescaler register (should be 0x53 = 83)
(gdb) print /t (TIM2->CNT)    # Current counter value
(gdb) shell sleep 1           # Wait 1 second
(gdb) print /t (TIM2->CNT)    # Read again (should be ~1000000 higher)
```

Expected results:
- TIM2->PSC = 0x53 (83 in decimal)
- Counter increases by ~1,000,000 every second

## Procedure 4: Correlate Pi Probe with STM32 Timestamps

**Use Case:** Pi probe measured offset_us = 500000 µs. What was the actual STM32 local time?

**Steps:**

1. **From Pi probe (spi_time_sync_probe.py output):**
   - Record pi_time_us at request time (T_start)
   - Record pi_time_us at response time (T_end)
   - Note: pi_time_us is approximate (uses monotonic clock on Pi side)

2. **From STM32 SWD (procedure above):**
   - Read `g_time_sync_dbg.pi_time_us` (STM32's captured Pi time)
   - Read `g_time_sync_dbg.local_capture_us` (STM32 local clock at capture)

3. **Calculate true offset:**
   ```
   true_offset_us = pi_time_us_stm32 - local_capture_us
   ```

4. **Compare with probe measurement:**
   - Probe estimated: offset_us = pi_time_us (from request) - 0 (placeholder)
   - True value: offset_us = pi_time_us_stm32 - local_capture_us
   - Delta should be < 1 ms (SYS-SYNC-001 target)

## Procedure 5: Export Data for Analysis

**Using OpenOCD scripting:**

Create an OpenOCD script, for example `dump_sync_data.ocd` (it is not in the repository):
```tcl
init
targets
halt
set pi_time [expr {[read_memory 0x20001234 32 1] & 0xFFFFFFFF}]
set local_time [expr {([read_memory 0x20001234 32 1] >> 32) & 0xFFFFFFFF}]
set result [expr {[read_memory 0x20001240 32 1] & 0xFFFFFFFF}]
puts "pi_time_us=$pi_time local_capture_us=$local_time result=$result"
shutdown
```

Run:
```bash
openocd -f interface/stlink-v2.cfg -f target/stm32f4x.cfg \
  -c "script dump_sync_data.ocd"
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "monitor reset halt" fails | Debugger not connected | Check USB cable to ST-Link |
| "print g_time_sync_dbg" shows "No symbol" | Firmware built without DEBUG=1 | Rebuild: `make clean; make DEBUG=1` |
| Counter increases > 1M/sec | Prescaler wrong | Check TIM2 init (main.c line 338) |
| Large offset jumps (>1ms) | Clock drift or incorrect capture | Run multiple readings, average |

## References

- SWD Protocol: [ARM AMBA AXI Specification](https://github.com/ARM-software/AMBA-AXI)
- OpenOCD Manual: [openocd.org](https://openocd.org/)
- STM32F405 Reference: [RM0090 STM32F405/415, STM32F407/417, STM32F427/437 and STM32F429/439 advanced ARM-based 32-bit MCUs](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405-415-stm32f407-417-stm32f427-437-and-stm32f429-439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
