Origin: backlog story B132 (WP10, "S10.16 SPI response path built once: the protocol module validates, calls one injected handler and writes the frame into the pool's buffer; the service becomes transport")

## Context

Today the SPI service validates a request, builds NACKs, overrides TIME_SYNC and keeps its own response and pending-request buffers, so the module mirrored by `spi_protocol.py` does not hold every message rule and validation can run twice. Every Pi-visible response should be decided and built in `spi_protocol.c` from one validation and one handler call, written once into the buffer the frame pool lends. Design settled with Lenton Neale on 2026-10-15 (architecture review, candidate 4).

## Scope

`spi_protocol.c`, `spi_slave_service.c` and their tests. Not covered: the DIAGNOSTIC, SET_MOTOR_COMMAND and system-activate handler cases, which later issues add as handler cases.

## Acceptance Criteria

- [ ] `SpiProtocol_ProcessRequest` validates framing once (magic, version, length, CRC, sequence, known type, R1 payload rule), advances the request-sequence mark on every frame-valid request whatever the handler answers (R3), calls the one injected handler, and writes the complete frame once; the service's own ValidateRequest, NACK building and TIME_SYNC override are gone
- [ ] The handler seam is one function injected at init, returning accepted with length or refused with NACK status and detail; the protocol module owns header, sequence, `frame_time_us`, `request_received_local_us` (on ACK, VERSION and SNAPSHOT, never NACK, omitted when no receipt time, R16), and CRC
- [ ] The service's handler is the application switch: BAD_STATE when the lifecycle disallows the type, GET_SNAPSHOT from a fresh coherent copy, GET_VERSION
- [ ] `SpiProtocol_StageUnsolicited` is the only other frame writer (boot and recovery DIAGNOSTIC, R14; periodic snapshot, PRM-ACQ-01)
- [ ] The frame pool lends its buffer, and `s_response_frame`, `unsolicited_payload` and `s_pending_request` are deleted (about 1.5 KB); the transmit sequence is consumed only for staged frames
- [ ] The pool's SNAPSHOT_FRAME_DMA_ACTIVE state is the one armed truth and `s_dma_active` is deleted
- [ ] `spi_slave_service.h` keeps seven entries (Init, Activate, GetLifecycleState, Process, the two HAL callbacks, GetSnapshotDiagnostics) and the listed exports are removed
- [ ] `protocol_test_main.c` tests each validation failure and NACK code, the R1 rule, the mark advancing on a refused request, receipt-time placement, the unsolicited path and the golden vectors against a scripted handler
- [ ] `FIRMWARE_ARCHITECTURE.md` describes the handler seam, and `SPI_SYSTEM_INTERFACE.md` sections 4 and 14 are named as implemented by `spi_protocol.c`
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests as listed; the stack check passes; the DMA-loop test in `service_test_main.c` asserts the pool state is the only armed flag.

## References

- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` sections 4 and 14
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (rulings R1, R3, R14, R16)
- `Arm_Sensor_Hub/Documentation/FIRMWARE_ARCHITECTURE.md`
