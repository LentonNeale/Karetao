# TODO List (Consolidated from existing repository documentation)

## docs/architecture.md
- Less mature or still being integrated: six-channel sensor scheduling.
- Less mature or still being integrated: final SPI DMA/NSS hardware integration.
- Less mature or still being integrated: complete TIME_SYNC dispatch through live SPI command handling.
- Less mature or still being integrated: expanded health aggregation.
- Less mature or still being integrated: end-to-end target-hardware evidence.

## docs/hardware/arm-sensor-hub-baseline.md
- Expand from single AS5600 bring-up to all six encoder channels via TCA9548A scheduling.
- Define and implement the SPI host contract to Raspberry Pi.
- Add CAN TX queueing policy, retry/timeout strategy, and bus-off recovery policy.
- Add integration tests for end-to-end sensor-to-host data path.

## docs/interfaces/spi-service-contract.md
- Hardware DMA invocation remains future work.
- Connect DMA/NSS handling and validate the 5 MHz initial maximum with Pi, DMA, GPIO, and signal-integrity tests.

## docs/protocols/spi-contract.md
- Maximum deployed clock rate remains an integration decision and must be frozen before DMA implementation.
- The exact record schema is a separate data-model decision and must be frozen before the encoder is implemented.
- The following remains an integration gate before SPI implementation is frozen: maximum SPI clock frequency and associated DMA timing.
- Lifecycle states permitted for each message type.

## docs/protocols/spi-payload-schema.md
- Event types and severity values remain reserved for the error-handling contract; values must be assigned before implementation.
- `SET_MOTOR_COMMAND` is not frozen until the Motor Service contract exists; it must not be implemented from this draft alone.
- Remaining schema decisions: exact event type and severity enumerations.
- Remaining schema decisions: whether diagnostic counters are 32-bit or 64-bit on the wire.
- Remaining schema decisions: snapshot dropped-count width and reset behavior.
- Remaining schema decisions: whether future records use a tagged extension mechanism.

## docs/interfaces/raspberry-pi-spi.md
- Confirm the final Linux SPI backend and bus/device path once Raspberry Pi OS packaging is chosen.
- Confirm `DATA_READY` GPIO polarity, debounce expectations, and user-space access strategy against target hardware.
- Confirm the maximum accepted SPI clock after the ARM-side 5 MHz integration gate is closed.
- Confirm final request/response retry policy for stalled or partial transactions.
- Confirm whether the Raspberry Pi should treat every transfer as fixed 512-byte frames or allow a future transport wrapper.

## RaspberryPi_Sensor_Hub/README.md
- Hardware-specific Linux SPI and GPIO choices remain TODO items until ARM contract gates are finalized.

## Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md (Next action column)
- Complete named CAN, SPI, motor, and safety gates.
- Implement prerequisite validation and explicit post-recovery activation request.
- Connect DMA/NSS handling and validate the 5 MHz initial maximum with Pi, DMA, GPIO, and signal-integrity tests.
- Validate exact controller, transceiver/topology/termination, candidate timing, measured load, retry timing, and recovery behavior.
- Extend coverage as more motor/sensor fields become live and retain target validation evidence.
- Expand producer coverage beyond the current commissioned sensor/motor set.
- Connect DMA/NSS events and complete documented Pi/DMA/GPIO clock acceptance testing.
- Expand composite-access coverage and define broader arbitration/recovery behavior.
- Implement complete six-channel scan and bind commissioned mapping/calibration versions.
- Validate end-to-end Pi-driven TIME_SYNC behavior on target hardware and retain build evidence.
- Define canonical CRC serialization and flash persistence/power-loss handling.
- Commission complete physical mapping and bind it to persisted configuration.
- Implement response-level events and bounded recovery escalation.
- Expand snapshot thresholds, host reporting cadence, and fault acknowledgement behavior.
- Install arm-none-eabi toolchain in the runner and re-run Debug/Release builds to retain target-build evidence.
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
- Debug configure is blocked by missing `arm-none-eabi-gcc/g++`.
- Re-establish target build evidence in CI/runner (P1, Blocking).
- Deepen negative-path coverage for hardware-facing service flows beyond smoke level (P2, Non-blocking follow-up).
- Clearance decision: `Blocked pending target build validation`.

## Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md
- Automated host tests were intentionally deferred from first implementation pass; required future cases remain listed.

## Arm_Sensor_Hub/Documentation/Conversations/CTO_DECISION_BRIEF.md
- CTO safety approval checklist items SD-02, SD-03, SD-04, SD-06, SD-05, SD-14, SD-20, SD-23, SD-24, and SD-25 remain unchecked.
- Open assumptions and integration gates 1 through 8 remain listed as open.
- Approval record SD-01 to SD-25 is pending.

## Arm_Sensor_Hub/Documentation/Sprint_1_List.md
- Remaining work (Task 07): canonical serialized CRC coverage using shared CRC-32/ISO-HDLC helper; redundant flash-sector allocation; erase/write ordering; endurance budget; power-loss recovery validation; wiring validated calibration state into mapping and lifecycle prerequisites.
- Remaining work (Task 08): complete physical commissioning; persisted configuration binding; future mapping schema for coupled/differential joints.
- Remaining work (Task 09): complete six-channel scanning and bind commissioned mapping/calibration versions to each record.
- Task 18 output is not implemented and deferred to when Motor Service work begins (open Sprint 2+ item).
- Sprint 1 exit criteria checklist items remain unchecked.

## Code vs document consistency issues found in code review
- `docs/interfaces/spi-service-contract.md` states fixed 512-byte request-frame validation, but `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py` still has an open TODO to confirm whether production transfers are fixed 512-byte frames.
- `docs/protocols/spi-contract.md` says the host shall validate `protocol_version`, but `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py` decode currently accepts any `protocol_version` value without rejecting unsupported versions.
- `docs/protocols/spi-contract.md` says the host shall track sequence numbers and reject stale/duplicate responses, but `RaspberryPi_Sensor_Hub/src/spi/spi_device.py` currently provides stateless transact/get_status helpers only.
- `docs/interfaces/raspberry-pi-spi.md` says production backend and bus/device path are not yet frozen; `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py` still carries placeholder defaults (`/dev/spidevTODO` and transfer `NotImplementedError`) that should be resolved once those contract gates are closed.
