# System Requirements

## Authority

This document is the authoritative Karetao system-requirement destination. Requirement statements are reconciled from the approved/modified Karetao system decisions and system-facing contracts. Each statement retains source provenance; decision records remain authoritative for decision status and rationale.

## Requirement baseline

| ID | Requirement | Source | Status / qualification |
|---|---|---|---|
| SYS-TIM-001 | The baseline sensor/state publication and initial control-loop rate shall be 100 Hz. | SD-01 | Baseline |
| SYS-TIM-002 | The EKF operating rate is 500 Hz unless downstream system constraints require adjustment. | SD-01 | Current setting; integration-dependent |
| SYS-TIM-003 | SPI initial maximum operating point is 5 MHz pending live integration and physical-layer validation. | SD-01, SD-15 | Provisional validation limit |
| SYS-FAIL-001 | A Raspberry Pi heartbeat timeout of 500 ms shall cause motion commands to be rejected. | SD-03 | Approved |
| SYS-FAIL-002 | On Raspberry Pi communication loss, the system shall perform a controlled stop where possible and then motor disable; it shall never hold the last motion command. | SD-03 | Approved; stop timing remains to be measured |
| SYS-FAIL-003 | Motor feedback timeout shall be based on five times the commissioned feedback period; one miss is degraded and three consecutive misses inhibit the motor and escalate to FAULT. | SD-04 | Approved |
| SYS-CAN-001 | The v1 CAN network shall target 1 Mbps nominal operation with standard 11-bit identifiers. | SD-05 | Modified; target-hardware validation required |
| SYS-CAN-002 | Average CAN load shall target less than 50–60% measured load. | SD-05 | Modified; measurement required |
| SYS-CAN-003 | CAN bus-off shall inhibit commands, perform bounded recovery, escalate after repeated failure, and require explicit reactivation. | SD-06 | Approved |
| SYS-MAP-001 | Logical-joint, sensor-ID and motor/CAN-ID mapping shall be deterministic and versioned, including direction, zero offset and transmission ratio. | SD-07 | Approved |
| SYS-TIM-004 | Normal observation skew shall be below 5 ms, with a target below 1 ms for dynamic joints; acquisition timestamps shall be retained. | SD-08 | Approved |
| SYS-CAL-001 | Calibration shall be computed on the Pi/workstation and transferred to the STM32 through a controlled validated configuration path. | SD-10 | Approved |
| SYS-CAL-002 | Calibration records shall be versioned, CRC-protected, redundant in STM32 flash, power-loss protected, and have a host-side source copy. | SD-11 | Approved; release conditions remain |
| SYS-IF-001 | Calibrated radians shall be authoritative at the host/API; wire-schema changes shall be explicitly versioned. | SD-12 | Modified |
| SYS-STATE-001 | Joint state shall include stable identity, position, available velocity, validity/status, acquisition timestamp, synchronization quality and calibration version. | SD-13 | Approved |
| SYS-CMD-001 | The command interface shall provide commissioned position/velocity plus enable, disable and controlled-stop operations, with heartbeat, lifecycle, calibration and safety gating. | SD-14 | Modified; acknowledgement/freshness details remain open |
| SYS-SPI-001 | SPI transactions shall use a 512-byte frame, maximum 490-byte payload, Mode 0, little-endian fields, CRC-32/ISO-HDLC and deterministic request/response ownership. | SD-15 | Approved |
| SYS-SPI-002 | Correlated GET_SNAPSHOT responses shall take priority; active DMA buffers shall remain immutable; replacement frames shall use replace-if-new semantics. | SD-16 | Approved; EKF state-age impact requires validation |
| SYS-SPI-003 | DATA_READY may provide latency notification and polling shall provide recovery; polling is initially 1 ms and the Pi is SPI clock master. | SD-17 | Approved; physical DATA_READY assignment remains unresolved |
| SYS-SYNC-001 | Timestamp error target shall be no more than ±1 ms relative to the shared STM32/Pi time model; synchronization validity and age shall be exposed. | SD-18 | Approved; adequacy for 500 Hz EKF requires validation |
| SYS-SYNC-002 | TIME_SYNC shall operate at 1 Hz nominal, configurable to 10 Hz; synchronization becomes invalid after five seconds without an accepted update. | SD-19 | Approved |
| SYS-SYNC-003 | When synchronization is invalid, acquisition and diagnostics shall continue but time-dependent motion shall be inhibited. | SD-20 | Modified; exact motion scope requires definition |
| SYS-SYNC-004 | Implausible time-offset updates shall be rejected without silent slew, using the approved wide-initial/narrow-runtime validation model. | SD-21 | Approved; numeric bounds require commissioning validation |
| SYS-SYNC-005 | Reset shall clear synchronization validity and volatile offset; timestamps remain unsynchronized until a new TIME_SYNC update is accepted. | SD-22 | Approved |
| SYS-REC-001 | Persistent/repeated/freshness failures shall enter ERROR; bounded recovery shall return to INACTIVE. | SD-23 | Approved; system-level motion gating during recovery requires explicit definition |
| SYS-REC-002 | System restart shall return to INACTIVE, use explicit dependency-ordered reactivation, and never automatically resume motor motion. | SD-24 | Approved |
| SYS-SAFE-001 | Independent E-stop, motor-disable/power-removal path, watchdog, stop/brake behaviour, fault indication, reset behaviour and applicable safety-rated architecture are release gates. | SD-25 | Modified; safety boundary follows risk assessment |
| SYS-MECH-001 | The differential end-effector motor-to-DOF mapping shall be represented explicitly rather than as independent one-to-one joints. | SD-26 | Proposed; do not treat as implemented until mechanical mapping is verified |

## Traceability rule

SD-01 through SD-26 have been systematically reviewed. The table above captures requirement-bearing system content identified during that review. Decision rationale, open issues and proposal status remain in the decision records. Component-only implementation constraints are not promoted to system requirements merely because they are normative in a component contract.

## Open requirement-definition items

- Assign final project requirement identifiers and acceptance criteria.
- Define the exact scope of “time-dependent motion” (SD-20).
- Define system motion-permission authority and recovery-in-progress gating (SD-02/SD-23).
- Define the safety boundary between application controlled-stop and independent safety functions (SD-25).
- Validate provisional CAN, SPI, timing and synchronization values on target hardware.
- Complete and verify the SD-26 mechanical transformation.
