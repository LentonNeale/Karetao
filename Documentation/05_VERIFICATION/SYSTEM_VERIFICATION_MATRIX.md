# System Verification Matrix

## Authority

This document is the authoritative Karetao system-level verification status record. Component verification remains component evidence and is not, by itself, system verification.

## Verification status

| Requirement | Code (module) | Test | Evidence required | Status | Accepted by / date |
|---|---|---|---|---|---|
| SYS-ENC-001 | `sensor_task.c`, `as5600.c`, `tca9548a_mux.c`, `snapshot_builder.c` | host: `service_smoke_tests`; bench: per-axis reading procedure | an evidence record per fitted axis showing a valid reading that changes with joint motion, with STM32 timestamp, firmware identity from `VERSION` | OPEN | — |
| SYS-ENC-002 | `sensor_task.c`, `snapshot_builder.c`, `spi_protocol.c`, `spi_protocol.py` | host: `sprint1_protocol_tests`; Pi: `test_spi_protocol.py` (NOT_FITTED decode); none yet for the NOT_FITTED behaviour (issue: LIVE-17) | evidence record with one axis marked not fitted: snapshot shows NOT_FITTED, no health fault, other axes normal | OPEN (not implemented) | — |
| SYS-ENC-003 | `app_init.c` (commissioning tables), `joint_mapping.c` | inspection at merge | the commissioning table in `SYSTEM_CONFIGURATION.md` §2.1 and `app_init.c` agree | OPEN | — |
| SYS-MOT-001 | `can_service.c`, `motor_latest_value.c`, `snapshot_builder.c`, `spi_protocol.py` | host: `service_smoke_tests`; bench: motor position procedure | evidence record with every registered motor powered: each motor record valid and following commanded motion; with one motor unpowered only its record stale | OPEN (one motor registered today) | — |
| SYS-MOT-002 | `can_service.c`, `motor_latest_value.c`, `health_monitor.c` | host: `service_smoke_tests`; bench: feedback interruption | evidence record: feedback interrupted on one motor, record stale within PRM-MOT-01, escalation per PRM-MOT-02 visible in diagnostics | OPEN | — |
| SYS-TS-001 | `sensor_task.c`, `can_service.c`, `time_service.c`, `time_sync_session.py` | host: `sprint1_protocol_tests`; Pi: `test_time_sync_session.py`, `test_timing.py`; bench: Stage 3 skew measurement | evidence record: per-record timestamps decoded on the Pi, spread consistent with PRM-ACQ-02, ClockSync conversion when valid (Gate A then Gate B, TIME_SYSTEM_INTERFACE.md §8) | OPEN (Pi-side conversion not implemented, GitHub #42) | — |
| SYS-LINK-001 | `motion_permission.c`, `spi_slave_service.c`, `time_service.c` | host: `sprint1_protocol_tests` (time_service), `service_smoke_tests` (spi_slave_service); link-loss detection: none yet (issue: LIVE-20) | evidence record: count-based detection within PRM-LINK-01 (interim 500 ms), commands rejected while `link_stale`, `link_stale` clears on the next accepted valid message | OPEN | — |
| SYS-LINK-002 | `motion_permission.c`, `spi_slave_service.c`, `can_service.c` | none yet (issue: LIVE-20); bench: link loss with a motor moving | evidence record: link loss observed: controlled stop then motor disable, with the timing measured, no last-command hold | OPEN | — |
| SYS-CAN-001 | `can_service.c`, `can_tx_policy.c` | host: `sprint1_protocol_tests` and `service_smoke_tests` (`can_tx_policy.c`); bench: bus-off induced | evidence record: live CAN bitrate and bus load per PRM-CAN-01; bus-off induced, motion commands inhibited, recovery steps per PRM-CAN-07/08 observed | OPEN | — |
| SYS-MAP-001 | `joint_mapping.c`, `app_init.c` | host: `sprint1_protocol_tests`, `service_smoke_tests` (`joint_mapping.c`) | motor half: the motor-to-joint mapping in `SYSTEM_CONFIGURATION.md` §2.1 and `app_init.c` agree and the mapped joint moves when its motor is commanded (differential end-effector verification: deferred (charter)) | OPEN; differential part deferred (charter) | — |
| SYS-CAL-001 | `calibration_record.c` | host: `sprint1_protocol_tests` (`calibration_record.c`); transfer path and recovery: none yet (issue: LIVE-08) | evidence record: calibration record versioned and integrity-checked, transferred through the controlled path, host copy matches, recovery from a corrupt record observed | OPEN | — |
| SYS-IF-001 | `snapshot_builder.c`, `spi_protocol.py` | host: `sprint1_protocol_tests`, `service_smoke_tests` (`snapshot_builder.c`); Pi: `test_spi_protocol.py` | evidence record: snapshot decoded on the Pi with joint angles in radians at PRM-REP-01 precision and the joint-state content present | OPEN | — |
| SYS-SPI-001 | `spi_protocol.c`, `spi_payload_layout.h`, `spi_slave_service.c`, `spi_data_ready.c`, `spi_protocol.py`, `spi_device.py` | host: `sprint1_protocol_tests`, `service_smoke_tests`; Pi: `test_spi_protocol.py`, `test_spi_device.py`, `test_data_ready_analysis.py`; bench: Stage 3 measurement | evidence record: live framing and CRC between Pi and STM32 at the PRM-SPI-01 clock and PRM-SPI-05 cable, replace-if-new behaviour, DATA_READY and polling both working | OPEN | — |
| SYS-CMD-001 | `spi_protocol.c`, `spi_slave_service.c`, `can_service.c`, `spi_protocol.py` | host: `sprint1_protocol_tests`; Pi: `test_spi_protocol.py`; bench: one command per kind | evidence record: each of enable, disable, stop, move-to-position, move-at-velocity ACKed and visible in the snapshot motor record | OPEN (not implemented, [LIVE-20]) | — |
| SYS-GATE-001 | `motion_permission.c`, `spi_slave_service.c`, `can_service.c` | none yet (issue: LIVE-20); bench: each input removed in turn | evidence record: SET_MOTOR_COMMAND NACKed with the matching reason for each removed input, ACKed with all present | OPEN (not implemented; code evaluates a superset) | — |
| SYS-REC-001 | `lifecycle.c`, `health_monitor.c`, `app_init.c` | host: `sprint1_protocol_tests`, `service_smoke_tests` (`lifecycle.c`, `health_monitor.c`); bench: fault then reset | evidence record: persistent fault enters ERROR, bounded recovery returns to INACTIVE; restart returns to INACTIVE and no motion resumes until explicitly re-enabled | OPEN | — |
| SYS-SYNC-001 | `time_service.c`, `spi_slave_service.c`, `time_sync_session.py` | host: `sprint1_protocol_tests`; Pi: `test_time_sync_session.py`, `test_time_sync_analysis.py`, `test_timing.py`, `test_validation_claims.py`; bench: Stage 3 measurement | evidence record: clock-sync observation in every applicable response, ClockSync valid/invalid and age exposed, STM32 reset invalidates the model, implausible observations rejected, error within PRM-TS-01 | OPEN (Issue #12 design and Pi conversion not implemented) | — |

## Verified motion per joint (charter goal 4)

| Requirement | Code (module) | Test | Evidence required | Status | Accepted by / date |
|---|---|---|---|---|---|
| Joint X verified motion | `motion_permission.c`, `can_service.c`, MKS controller | bench procedure (gated command) | (a) initial movement record, written by Lenton Neale from the tests already done, dated; (b) a command passed through the gate (ACK with reason ALLOWED, motion visible in the snapshot motor record); (c) stop on link loss observed (SAFE-02) | OPEN (initial movement seen, commanded by an earlier firmware build at the MKS factory-default CAN rate (Lenton Neale, 2026-10-15; ruling R9c); record not yet written; axis number unknown, see `SYSTEM_CONFIGURATION.md` §2.1) | — |
| Joint Y verified motion | `motion_permission.c`, `can_service.c`, MKS controller | bench procedure (gated command) | (a) initial movement record, written by Lenton Neale from the tests already done, dated; (b) a command passed through the gate (ACK with reason ALLOWED, motion visible in the snapshot motor record); (c) stop on link loss observed (SAFE-02) | OPEN (initial movement seen, commanded by an earlier firmware build at the MKS factory-default CAN rate (Lenton Neale, 2026-10-15; ruling R9c); record not yet written; axis number unknown, see `SYSTEM_CONFIGURATION.md` §2.1) | — |
| Joint Z verified motion | `motion_permission.c`, `can_service.c`, MKS controller | bench procedure (gated command) | (a) initial movement record, written by Lenton Neale from the tests already done, dated; (b) a command passed through the gate (ACK with reason ALLOWED, motion visible in the snapshot motor record); (c) stop on link loss observed (SAFE-02) | OPEN (initial movement seen, commanded by an earlier firmware build at the MKS factory-default CAN rate (Lenton Neale, 2026-10-15; ruling R9c); record not yet written; axis number unknown, see `SYSTEM_CONFIGURATION.md` §2.1) | — |
| Joint 4 verified motion (name unknown) | `motion_permission.c`, `can_service.c`, MKS controller | bench procedure (gated command) | as for Joint X | NOT STARTED (hardware unconfirmed) | — |
| Joint 5 verified motion (name unknown) | `motion_permission.c`, `can_service.c`, MKS controller | bench procedure (gated command) | as for Joint X | NOT STARTED (hardware unconfirmed) | — |
| Joint 6 verified motion (name unknown) | `motion_permission.c`, `can_service.c`, MKS controller | bench procedure (gated command) | as for Joint X | NOT STARTED (hardware unconfirmed) | — |

## Safety behaviours

| Requirement | Code (module) | Test | Evidence required | Status | Accepted by / date |
|---|---|---|---|---|---|
| SAFE-01 | hardware | bench | evidence record: power cut or E-stop operated by hand removes motor power, observed, without relying on firmware | OPEN | — |
| SAFE-02 | `spi_slave_service.c`, `motion_permission.c` | bench | evidence record: link loss observed: motors stop, then are disabled, within the stated time | OPEN | — |
| SAFE-03 | `can_service.c`, `can_tx_policy.c` | bench | evidence record: bus-off induced: motion commands inhibited and recovery observed | OPEN | — |
| SAFE-04 | `lifecycle.c`, `app_init.c` | bench | evidence record: reset of the STM32 observed: no motion resumes until explicitly re-enabled | OPEN | — |
| SAFE-05 | `health_monitor.c` | bench | evidence record: each fault induced is visible in the snapshot or diagnostics | OPEN | — |

## Status rule

`SYSTEM_VERIFIED` may be assigned only by Karetao system verification after integrated evidence is accepted. Component `VERIFIED` or `HARDWARE_VERIFIED` status does not automatically establish `SYSTEM_VERIFIED`.

A row supports SYSTEM_VERIFIED only when evidence demonstrates the requirement at integration scope and Lenton Neale has accepted it; passing a component test alone does not close a row (former INTEGRATION_GATES.md, merged 2026-10-03).

## Traceability

Primary requirement source is `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`; source decision IDs are retained there. Component test results are evidence inputs and must be linked when accepted. Evidence records follow `EVIDENCE_RECORD_FORMAT.md`; a record from a dirty firmware build does not satisfy a row.

Evidence records live under 05_VERIFICATION/evidence/ (none yet).
