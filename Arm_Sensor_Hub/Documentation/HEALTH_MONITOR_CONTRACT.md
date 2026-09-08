# Health Monitor Contract

**Status:** Design target  
**Owner:** `HealthMonitor`  
**Boundary:** Service diagnostics -> aggregate system health and reporting

## Role

HealthMonitor observes lifecycle records, service counters, timestamps, and fault summaries. It does not own peripheral recovery, activate dependencies, or replace service-specific diagnostics.

## Health Levels

Proposed levels:

- `UNKNOWN`: startup or insufficient evidence;
- `GREEN`: required services operational with no active persistent faults;
- `YELLOW`: degraded service, stale/partial sensor data, or recoverable faults;
- `RED`: required service in `ERROR`, unsafe motor condition, or fatal system fault.

The required-service set must be defined by operating mode.

## Observations

At minimum observe I2C lifecycle/error/timeout counters, sensor channel validity and age, CAN lifecycle/TX/RX/decode/bus diagnostics, SPI lifecycle/DMA/drop/sync diagnostics, and application registration failures.

HealthMonitor shall expose a consistent snapshot containing aggregate level, active fault, last-fault timestamp, service states, and key counters. Snapshot ownership must be read-only to callers.

All diagnostic timestamps use the shared 64-bit monotonic time extension. Synchronization quality is `valid` only when the last accepted TIME_SYNC update is no older than 5 seconds; otherwise diagnostics report unsynchronized/stale time.

## Runtime and RTOS

`HealthMonitor_Process()` runs in task context at a bounded rate. Diagnostic reads must not block service operations. ISR code may update atomic counters or pending flags but must not call health aggregation or publish messages.

## Reporting and Recovery

HealthMonitor may publish diagnostic data through SPI when available and retain it locally otherwise. It reports recovery recommendations or requests through an explicit future API; it does not silently perform recovery in the initial implementation.

Watchdog ownership is open. No watchdog kick or reset policy should be inferred from this contract until system safety review approves it.

## Startup and Shutdown

Startup health is `UNKNOWN` until required services report configured/active status. Shutdown preserves the last health snapshot and records the shutdown reason.

## Open Decisions

- required service set per operating mode;
- exact thresholds for GREEN/YELLOW/RED;
- diagnostic snapshot structure;
- watchdog owner and timeout;
- host reporting cadence;
- fault acknowledgement and clear rules.
