⚠ **ARCHIVED — Non-normative historical document**

- **Archived:** 2026-09-20
- **Historical status:** Superseded by current decision register
- **Superseded by:** `07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md`

---

# TODO List (Consolidated from existing repository documentation)

## docs/architecture.md
- Less mature or still being integrated: live Raspberry Pi <-> STM32 SPI transaction acceptance.
- Less mature or still being integrated: 5 MHz physical SPI acceptance, including DMA timing, NSS, DATA_READY/GPIO timing, and signal integrity.
- Less mature or still being integrated: sustained/repeated SPI transaction validation.
- Less mature or still being integrated: scan timing and other six-channel sensor parameters that remain unfrozen.
- Less mature or still being integrated: complete TIME_SYNC target validation.
- Less mature or still being integrated: expanded health aggregation.
- Less mature or still being integrated: CAN physical validation.
- Less mature or still being integrated: calibration persistence.
- Less mature or still being integrated: exact motor-controller semantics.
- Less mature or still being integrated: independent safety validation.

## docs/hardware/arm-sensor-hub-baseline.md
- Add CAN TX queueing policy, retry/timeout strategy, and bus-off recovery policy.
- Add integration tests for end-to-end sensor-to-host data path.
- Retain live SPI host validation, 5 MHz physical acceptance, and DATA_READY/NSS electrical validation as integration gates.

## docs/interfaces/spi-service-contract.md
- Validate the implemented DMA/NSS path with a live Raspberry Pi host.
- Validate the 5 MHz initial maximum with Pi, DMA, GPIO, NSS, and signal-integrity tests.

## docs/protocols/spi-contract.md
- Validate the implemented SPI3 DMA path with a live Raspberry Pi host.
- Accept the 5 MHz maximum only after DMA timing, NSS behavior, DATA_READY/GPIO timing, signal integrity, sustained transactions, and real request/response evidence are recorded.
- Retain the existing protocol/schema freeze decisions; do not turn implementation details into new requirements.
- Lifecycle states permitted for each message type.

## docs/protocols/spi-payload-schema.md
- Event types and severity values remain reserved for the error-handling contract; values must be assigned before implementation.
- `SET_MOTOR_COMMAND` is not frozen until the Motor Service contract exists; it must not be implemented from this draft alone.
- Remaining schema decisions: exact event type and severity enumerations.
- Remaining schema decisions: whether diagnostic counters are 32-bit or 64-bit on the wire.
- Remaining schema decisions: snapshot dropped-count width and reset behavior.
- Remaining schema decisions: whether future records use a tagged extension mechanism.

## docs/interfaces/raspberry-pi-spi.md
- Confirm `DATA_READY` GPIO polarity, debounce expectations, and user-space access strategy against target hardware; the Raspberry Pi GPIO remains intentionally unassigned in the current baseline.
- Confirm the maximum accepted SPI clock after the ARM-side 5 MHz integration gate is closed.
- Confirm final request/response retry policy for stalled or partial transactions.
- Retain fixed 512-byte transfers as the current transport implementation; revisit only through a versioned contract change.

## RaspberryPi_Sensor_Hub/README.md
- Validate the implemented Linux `spidev` backend on the target Raspberry Pi.
- Close the DATA_READY GPIO integration decision only when a Raspberry Pi GPIO is actually assigned and validated.

## Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md (Next action column)
- Complete named CAN, SPI, motor, and safety gates.
- Implement prerequisite validation and explicit post-recovery activation request.
- Validate the 5 MHz initial SPI maximum with Pi, DMA, GPIO, NSS, and signal-integrity tests.
- Validate exact controller, transceiver/topology/termination, candidate timing, measured load, retry timing, and recovery behavior.
- Extend coverage as more motor/sensor fields become live and retain target validation evidence.
- Expand producer coverage beyond the current commissioned sensor/motor set.
- Complete documented Pi/DMA/GPIO clock acceptance testing with a live host.
- Expand composite-access coverage and define broader arbitration/recovery behavior.
- Freeze scan period, per-channel timeout, settle time, and healthy-channel threshold against the measured ~46 ms full-six-axis sweep.
- Validate end-to-end Pi-driven TIME_SYNC behavior on target hardware and retain build evidence.
- Define canonical CRC serialization and flash persistence/power-loss handling.
- Commission complete physical mapping and bind it to persisted configuration.
- Implement response-level events and bounded recovery escalation.
- Expand snapshot thresholds, host reporting cadence, and fault acknowledgement behavior.
- Preserve the successful CI firmware-build evidence, size/checksum output, and uploaded artifacts.
- Verify exact controller behavior before freezing command semantics.

## Arm_Sensor_Hub/Documentation/Module_TODOs/CAN_Module_TODO.md
- Confirm transceiver wiring: CAN1_TX -> TJA1050 TXD, CAN1_RX -> TJA1050 RXD, shared GND, and stable 5V/3.3V domain compatibility.
- Add/verify proper 120-ohm termination at both physical bus ends.
- Validate CANH/CANL idle and dominant levels with scope or analyzer before motion commands.
- Document the exact bench topology (cable length, stubs, node count, termination locations).
- Decide initial real-test bitrate (e.g., 500 kbps or 1 Mbps) and update CubeMX/HAL CAN timing settings to match measured behavior.
- Verify CANable V2 bitrate matches STM32 bitrate exactly.
- Re-check sample point/SJW margin against oscillator tolerance for STM32 + bus layout.
- Record finalized timing values and rationale in `Documentation/CAN_BIT_TIMING_EVIDENCE.md`.
- Add duplicate CAN ID rejection in `CanService_RegisterMotor()` to prevent ambiguous RX frame ownership.
- Add explicit HAL error diagnostics mapping (TX/RX/error counters by error class).
- Add RX FIFO overflow tracking/handling and expose it through CAN diagnostics.
- Define and implement response timeout expectations per poll/command path.
- Confirm emergency-stop behavior policy during lifecycle `ERROR` and enforce/document selected behavior.
- Expose runtime CAN diagnostics in a host-visible channel (SPI snapshot/log/telemetry): lifecycle state, bus-off count, queue drops, retry-exhausted count, RX ok/decode error counts.
- Add timestamped trace points for command TX, response RX, and bus-off recovery attempts.
- Add a simple bench-test checklist to log pass/fail for power-up, idle, command, and fault-recovery scenarios.
- Create a repeatable CANable capture script/procedure (startup capture, command-response capture, fault injection capture).
- Validate that expected MKS command IDs and response frames appear on the bus with correct DLC/payload.
- Verify poll traffic cadence at default 20 ms scheduler period and confirm no unintended bus flooding.
- Run long-duration soak capture to check for dropped frames, decode errors, or recurring bus-off.
- Test bus disconnection/reconnection and confirm bus-off detection, inhibition of normal commands, and recovery back to inactive state.
- Confirm `CanService_Activate()` is required and sufficient to re-enable normal commands after recovery.
- Test mailbox pressure/temporary TX failures and validate retry and drop diagnostics behavior.
- Verify behavior when receiving unknown CAN IDs and malformed DLC/payload frames.
- Add host-side tests for `can_service` logic that does not require real CAN hardware (registration constraints, scheduler behavior, queue/retry edge cases via mocks).
- Add hardware-in-the-loop test notes for STM32 + TJA1050 + CANable in Documentation with required tooling and expected outputs.
- Update contract status once integration gates are closed with measured evidence.
- Expand `s_mks_motors` and joint mapping only after each added motor passes single-node bench validation.
- Validate per-motor direction, ID, and mapping consistency before enabling multi-motor motion tests.
- Freeze a known-good CAN commissioning baseline (timing + topology + firmware revision + test evidence).

## Arm_Sensor_Hub/Documentation/SAFETY_RELEASE_CHECKLIST.md
- Machine risk assessment and required PL/SIL target — BLOCKED: no artifact recorded.
- Independent E-stop path — BLOCKED: no artifact recorded.
- Hardware motor-disable or power-removal path — BLOCKED: no artifact recorded.
- Watchdog behavior and fault recovery — BLOCKED: no artifact recorded.
- Actuator stop/brake/power behavior — BLOCKED: no artifact recorded.
- Fault indication and operator-visible reporting — BLOCKED: no artifact recorded.
- Reset behavior and explicit non-automatic reactivation — BLOCKED: no artifact recorded.
- Measured stopping time in hazardous operating conditions — BLOCKED: no artifact recorded.
- Exact MKS controller model, firmware, command, feedback, and brake behavior — BLOCKED: no artifact recorded.
- CAN physical layer, bitrate, load, termination, topology, and recovery — BLOCKED: no artifact recorded.
- SPI clock, Pi driver, DMA, GPIO, polling, host-stall, and signal-integrity acceptance — BLOCKED: no artifact recorded.
- Versioned payload schema and conversion evidence before replacing processed millidegrees with radians — BLOCKED: no artifact recorded.
- Calibration flash schema, CRC, power-loss, sector allocation, and endurance test evidence — BLOCKED: no artifact recorded.
- Applicable safety-rated relay/controller and safety architecture — BLOCKED: no artifact recorded.

## Arm_Sensor_Hub/Documentation/PHASE_1_FINAL_CLEARANCE_REPORT.md
- Historical report dated 2026-09-07 recorded missing ARM toolchain evidence at that review point. Do not treat that historical finding as the current repository build state; current CI evidence is tracked in `BUILD_CONTRACT.md` and `CONTRACT_STATUS.md`.
- Deepen negative-path coverage for hardware-facing service flows beyond smoke level (P2, Non-blocking follow-up).

## Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md
- Automated host tests were intentionally deferred from first implementation pass; required future cases remain listed.

## Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_BRIEF.md
- CTO safety approval checklist items SD-02, SD-03, SD-04, SD-06, SD-05, SD-14, SD-20, SD-23, SD-24, and SD-25 remain unchecked.
- Open assumptions and integration gates 1 through 8 remain listed as open.
- Approval record SD-01 to SD-25 is pending.

## Arm_Sensor_Hub/Documentation/Sprint_1_List.md
- Remaining work (Task 07): canonical serialized CRC coverage using shared CRC-32/ISO-HDLC helper; redundant flash-sector allocation; erase/write ordering; endurance budget; power-loss recovery validation; wiring validated calibration state into mapping and lifecycle prerequisites.
- Remaining work (Task 08): complete physical commissioning; persisted configuration binding; future mapping schema for coupled/differential joints.
- Remaining work (Task 09): freeze scan timing parameters against the commissioned SD2-SD7 mapping and measured ~46 ms full-axis sweep; calibration binding remains open.
- Task 18 output is not implemented and deferred to when Motor Service work begins (open Sprint 2+ item).
- Sprint 1 exit criteria checklist items remain unchecked.

## Code vs document consistency issues found in code review
- `spi_device.py` still provides stateless `transact/get_status` helpers; do not claim complete host-side outstanding-transaction state tracking merely because frame-level sequence/version validation exists.
- Live Pi/STM32 request/response, DATA_READY GPIO assignment, NSS behavior, 5 MHz acceptance, and signal integrity remain physical validation work rather than implementation TODOs.
