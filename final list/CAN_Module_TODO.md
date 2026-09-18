# CAN Module TODO (STM32 + TJA1050 + CANable V2)

## Current State Review

- `CanService` is implemented with lifecycle gating, motor registration, TX priority queue, bounded retries, RX decode path, and bus-off recovery scaffolding (`App/Src/can_service.c`).
- CAN runs in normal mode and is processed in the default FreeRTOS task loop through `CanService_Process()` (`Core/Src/main.c`).
- Hardware pins are configured for CAN1 on `PB8` (RX) and `PB9` (TX) (`Core/Src/stm32f4xx_hal_msp.c`).
- Only one motor is currently pre-registered in app startup config (`App/Src/app_init.c`).
- Current generated CAN timing is `Prescaler=16`, `BS1=11TQ`, `BS2=2TQ` (not yet aligned to a validated real-hardware target) (`Core/Src/main.c`).
- Host tests currently cover `can_tx_policy.c`, but not full `can_service.c` behavior with HAL integration (`tests/host/CMakeLists.txt`).
- Existing docs already mark CAN bitrate/physical-layer validation as an integration gate (`Documentation/CAN_SERVICE_CONTRACT.md`, `Documentation/CAN_BIT_TIMING_EVIDENCE.md`).

## TODO List for Real-Life Bring-Up and Testing

### 1) Hardware Bring-Up (STM32 + TJA1050)
- [ ] Confirm transceiver wiring: CAN1_TX -> TJA1050 TXD, CAN1_RX -> TJA1050 RXD, shared GND, and stable 5V/3.3V domain compatibility.
- [ ] Add/verify proper 120-ohm termination at both physical bus ends.
- [ ] Validate CANH/CANL idle and dominant levels with scope or analyzer before motion commands.
- [ ] Document the exact bench topology (cable length, stubs, node count, termination locations).

### 2) Bitrate and Controller Configuration
- [ ] Decide initial real-test bitrate (e.g., 500 kbps or 1 Mbps) and update CubeMX/HAL CAN timing settings to match measured behavior.
- [ ] Verify CANable V2 bitrate matches STM32 bitrate exactly.
- [ ] Re-check sample point/SJW margin against oscillator tolerance for STM32 + bus layout.
- [ ] Record finalized timing values and rationale in `Documentation/CAN_BIT_TIMING_EVIDENCE.md`.

### 3) Firmware Readiness Gaps Before Bench Motion
- [ ] Add duplicate CAN ID rejection in `CanService_RegisterMotor()` to prevent ambiguous RX frame ownership.
- [ ] Add explicit HAL error diagnostics mapping (TX/RX/error counters by error class).
- [ ] Add RX FIFO overflow tracking/handling and expose it through CAN diagnostics.
- [ ] Define and implement response timeout expectations per poll/command path.
- [ ] Confirm emergency-stop behavior policy during lifecycle `ERROR` and enforce/document selected behavior.

### 4) Observability for Bench Testing
- [ ] Expose runtime CAN diagnostics in a host-visible channel (SPI snapshot/log/telemetry): lifecycle state, bus-off count, queue drops, retry-exhausted count, RX ok/decode error counts.
- [ ] Add timestamped trace points for command TX, response RX, and bus-off recovery attempts.
- [ ] Add a simple bench-test checklist to log pass/fail for power-up, idle, command, and fault-recovery scenarios.

### 5) CANable V2 Test Procedure
- [ ] Create a repeatable CANable capture script/procedure (startup capture, command-response capture, fault injection capture).
- [ ] Validate that expected MKS command IDs and response frames appear on the bus with correct DLC/payload.
- [ ] Verify poll traffic cadence at default 20 ms scheduler period and confirm no unintended bus flooding.
- [ ] Run long-duration soak capture to check for dropped frames, decode errors, or recurring bus-off.

### 6) Fault Injection and Recovery Validation
- [ ] Test bus disconnection/reconnection and confirm bus-off detection, inhibition of normal commands, and recovery back to inactive state.
- [ ] Confirm `CanService_Activate()` is required and sufficient to re-enable normal commands after recovery.
- [ ] Test mailbox pressure/temporary TX failures and validate retry and drop diagnostics behavior.
- [ ] Verify behavior when receiving unknown CAN IDs and malformed DLC/payload frames.

### 7) Test Coverage and Automation
- [ ] Add host-side tests for `can_service` logic that does not require real CAN hardware (registration constraints, scheduler behavior, queue/retry edge cases via mocks).
- [ ] Add hardware-in-the-loop test notes for STM32 + TJA1050 + CANable in Documentation with required tooling and expected outputs.
- [ ] Update contract status once integration gates are closed with measured evidence.

### 8) Commissioning Expansion
- [ ] Expand `s_mks_motors` and joint mapping only after each added motor passes single-node bench validation.
- [ ] Validate per-motor direction, ID, and mapping consistency before enabling multi-motor motion tests.
- [ ] Freeze a known-good CAN commissioning baseline (timing + topology + firmware revision + test evidence).
