# Parameter register

Status: Working values, 2026-10-03. Owner: Lenton Neale.

Role: this register is the only home for tunable and physical values (SPI clock, CAN bitrate, sync skew, poll periods, loss behaviour, timing budgets). Requirements and interface documents reference entries by ID and never restate the value. Charter goal 3 (`../01_SYSTEM/PROJECT_CHARTER.md`) is the authority for the basis vocabulary.

## Basis vocabulary

| Basis | Meaning |
|---|---|
| Measured | A dated measurement record exists and is linked in the Source column. |
| Datasheet | A vendor datasheet or reference manual states it; the section is cited. |
| Derived | Calculated from Measured or Datasheet values; the calculation is shown. |
| Provisional | An engineering estimate not yet confirmed. A working value, never a requirement. |

## Rules

- A Provisional value is a working value and never a requirement.
- A basis changes only when the evidence is linked in the Source column.
- Contract constants (magic `0xA55A`, 18-byte header, CRC-32/ISO-HDLC, 512-byte frame, 490-byte payload, 24-byte records, message type values, lifecycle state names) are not parameters and stay in the interface documents.
- A code default that differs from the register's working value is recorded as a divergence in the Notes column, not silently changed.
- The 500 Hz EKF rate is withdrawn (charter non-goal) and is not registered.

## Register

Code symbols were checked against `Arm_Sensor_Hub/App` on 2026-10-03.

### Acquisition (ACQ)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-ACQ-01 | Sensor and snapshot publication rate | 20 | Hz | Provisional | bounded by the measured sweep PRM-ACQ-02 (≈46 ms); SD-01's 100 Hz is the former target, reachable only after the sweep is shortened toward PRM-ACQ-03 | 2026-10-03 | SYS-ENC, SYS-MOT | Demoted from 100 Hz on 2026-10-03 (Lenton Neale). Stage 3 measures the achieved rate. |
| PRM-ACQ-02 | Six-axis encoder sweep time | ≈ 46 | ms | Measured | `tools/check-sensors.sh` run; archived `CONTRACT_STATUS.md` in git history | 2026-09-17 | SYS-TS-001 | The only Measured row. |
| PRM-ACQ-03 | I2C protocol floor for six sensors | ≈ 690 | µs | Derived | `I2C_SCAN_TIMING_ANALYSIS.md` (AS5600 datasheet, 400 kHz) | 2026-10-03 | improvement target only | Theoretical floor, not a measurement. |
| PRM-ACQ-04 | I2C bus clock | 400 | kHz | Datasheet | AS5600 and TCA9548A fast mode; CubeMX `.ioc` | 2026-10-03 | sensor path | none |
| PRM-ACQ-05 | Sensor task poll period | 20 | ms | Provisional | `SENSOR_TASK_BRINGUP_POLL_PERIOD_MS`, `sensor_task.c` | 2026-10-03 | sensor path | Code default is 20 ms, which is 50 Hz and differs from PRM-ACQ-01 (100 Hz). Recorded, not changed. |
| PRM-ACQ-06 | AS5600 resolution | 12 bit, 4096 codes/rev, ≈ 0.001534 rad/code | bit, rad | Datasheet | AS5600 datasheet; `AS5600_PRECISION_AND_ACCURACY.md` | 2026-10-03 | SYS-IF-001 | none |

### SPI link (SPI)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-SPI-01 | SPI clock, maximum | 5 | MHz | Provisional | SD-01, SD-15 | 2026-10-03 | SYS-SPI-001; Stage 3 measurement | A ceiling, not approval. |
| PRM-SPI-02 | Wire time per 512-byte frame at PRM-SPI-01 | 819.2 | µs | Derived | 512 × 8 / 5 MHz | 2026-10-03 | link budget | Changes with PRM-SPI-01. |
| PRM-SPI-03 | Host polling fallback period | 1 | ms | Provisional | SD-17; `SPI_SERVICE_DEFAULT_POLL_PERIOD_MS`, `spi_slave_service.c` | 2026-10-03 | SPI host | Code default matches. |
| PRM-SPI-04 | Host-stall timeout | 100 | ms | Provisional | `SPI_SERVICE_HOST_STALL_MS`, `spi_slave_service.c` | 2026-10-03 | SPI slave | Code default matches. |
| PRM-SPI-05 | SPI cable length | 20–30 | cm | Provisional | former SYS-SPI-004 | 2026-10-03 | Stage 3 measurement | none |

### CAN (CAN)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-CAN-01 | CAN bitrate target | 1 | Mbps | Provisional | SD-05 | 2026-10-03 | SYS-CAN-001 | Target, not yet applied (see PRM-CAN-02, -03). |
| PRM-CAN-02 | CAN bitrate as generated | 875 (prescaler 16, BS1 1, BS2 1, SJW 1, sample point 66.7 %, APB1 42 MHz) | kbps | Derived | `CAN_INTEGRATION_EVIDENCE.md`; `.ioc` | 2026-10-03 | as-built | Differs from PRM-CAN-01. |
| PRM-CAN-03 | Candidate 1 Mbps bit timing | prescaler 3, BS1 11, BS2 2, SJW 1, sample point 85.7 % | n/a | Derived (not applied) | `CAN_INTEGRATION_EVIDENCE.md` | 2026-10-03 | Stage 3 | Not applied to the `.ioc`. |
| PRM-CAN-04 | Average bus load ceiling | < 50–60 | % | Provisional | SD-05 | 2026-10-03 | Stage 3 measurement | none |
| PRM-CAN-05 | Motor poll period | 20 | ms | Provisional | `CAN_SERVICE_DEFAULT_POLL_PERIOD_MS`, `can_service.c` | 2026-10-03 | SYS-MOT-001 | Code default matches. |
| PRM-CAN-06 | TX HAL retry limit | 3 | count | Provisional | `CAN_SYSTEM_INTERFACE.md` §4; `CAN_SERVICE_MAX_TX_RETRIES`, `can_service.c` | 2026-10-03 | CAN transport | Code default matches. |
| PRM-CAN-07 | Bus-off recovery delays | 100 ms, doubling per failed recovery, capped at 1 s | ms | Derived | `CAN_BUS_OFF_INITIAL_DELAY_MS`, `CAN_BUS_OFF_MAX_DELAY_MS` and the doubling rule in `CanBusOff_*`, `can_tx_policy.c` | 2026-10-03 | SYS-CAN-001 | Adopted from the code on 2026-10-03 (Lenton Neale); the former 100/500/1000 ms steps had no basis. The 1 s cap is confirmed by the Stage 3 bus-off test. |
| PRM-CAN-08 | Bus-off escalation to ERROR | 3 events in 60 s | events, s | Provisional | `CAN_SYSTEM_INTERFACE.md` §5; `CAN_BUS_OFF_WINDOW_MS` and the `bus_off_events >= 3u` test in `CanBusOff_Record`, `can_tx_policy.c` | 2026-10-03 | SYS-CAN-001 | Code default matches. The count 3 is a literal, not a named symbol. |

### Motor feedback (MOT)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-MOT-01 | Motor feedback timeout | 5 × commissioned feedback period | multiple | Provisional | SD-04 | 2026-10-03 | SYS-MOT-002 | none |
| PRM-MOT-02 | Feedback miss handling | 1 miss degraded; 3 consecutive inhibit and FAULT | count | Provisional | SD-04 | 2026-10-03 | SYS-MOT-002 | none |

### Pi link liveness (LINK)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-LINK-01 | Pi link-loss detection limit (interim) | 500 | ms | Provisional | SD-03; Issue #12 item 11 | 2026-10-03 | SYS-LINK-001 | A 500 ms value exists in code as `MOTION_PERMISSION_HEARTBEAT_TIMEOUT_US`, `motion_permission.c`. Whether it is the same quantity is not confirmed. |
| PRM-LINK-02 | `N_moving`, `N_idle` | open | n/a | Provisional (no value) | Issue #12 item 11 | 2026-10-03 | SYS-LINK-001 | No value yet. |

### Timestamps and clock sync (TS)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-TS-01 | Timestamp error target | ± 1 | ms | Provisional | SD-18 | 2026-10-03 | SYS-TS-001; Stage 3 | none |
| PRM-TS-02 | Observation skew within a snapshot | < 5 normal; < 1 target for dynamic joints | ms | Provisional | SD-08 | 2026-10-03 | SYS-TS-001 | none |
| PRM-TS-03 | ClockSync validity window | 5 | s | Provisional | SD-19; as-built `TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US`, `time_service.h` | 2026-10-03 | SYS-TS-001, lifecycle | Code default matches. |
| PRM-TS-04 | `counter_extension_gap_us` | 500 | ms | Provisional | Issue #12 item 11 | 2026-10-03 | time service | no symbol found in code (2026-10-03); searched `counter_extension`, `extension_gap`, `gap` in `Arm_Sensor_Hub/App`. |
| PRM-TS-05 | Legacy drift bounds (as-built TIME_SYNC) | ± 24 h initial; ± 1 s runtime step | h, s | Provisional | as-built `TIME_SERVICE_DEFAULT_INITIAL_OFFSET_LIMIT_US` (86400000000 µs) and `TIME_SERVICE_DEFAULT_RUNTIME_OFFSET_STEP_LIMIT_US` (1000000 µs), `time_service.h` | 2026-10-03 | as-built only | Removed with Issue #12. |
| PRM-TS-06 | ClockSync plausibility rejection | half round-trip > 2 × running minimum half round-trip, or offset residual > PRM-TS-01 | ratio, ms | Provisional | decided 2026-10-15 (Lenton Neale) for the Issue #42 Gate A tests; the values are confirmed or revised from the Gate A synthetic and integration data | 2026-10-15 | SYS-TS-001; Pi ClockSync model (#42) | A rejected exchange is counted (`rejected_sample_count`) and does not update the model. Replaces the retired PRM-TS-05 bounds. |

### Representation (REP)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-REP-01 | External angle precision | 4 decimal places (0.0001 rad) | rad | Derived | SD-12 from PRM-ACQ-06 | 2026-10-03 | SYS-IF-001 | none |

### MCU (MCU)

| ID | Parameter | Working value | Unit | Basis | Source or evidence | Date | Used by | Notes |
|---|---|---|---|---|---|---|---|---|
| PRM-MCU-01 | Core clocks | SYSCLK 168; APB1 42; APB2 84 | MHz | Datasheet | STM32F405 and CubeMX `.ioc` | 2026-10-03 | CAN and SPI timing | none |
| PRM-MCU-02 | STM32F405 flash endurance | 10 | kcycles | Datasheet | STM32F405xx/407xx datasheet DS8626 §5.3.13 "Flash memory endurance and data retention", N_END minimum | 2026-10-15 | calibration records, SYSTEM_CONFIGURATION.md §3 | A calibration record is written once per calibration event, so endurance is not a requirement and no evidence is produced for it (ruled 2026-10-15, Lenton Neale). |

## Measurement stages

Stage 3 (Links measured) is expected to move these rows from Provisional to Measured, each with a linked dated measurement record: PRM-SPI-01, PRM-SPI-05, PRM-CAN-01, PRM-CAN-02, PRM-CAN-04, PRM-TS-01, PRM-TS-02, PRM-LINK-01, PRM-LINK-02, PRM-ACQ-01, PRM-ACQ-05.
