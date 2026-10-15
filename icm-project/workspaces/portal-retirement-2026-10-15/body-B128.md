Origin: backlog story B128 (WP10, "S10.15 Latest-value store: one module owns sample and feedback ageing, stale, and the coherent snapshot copy")

## Context

Snapshot coherency (`SPI_SYSTEM_INTERFACE.md` section 8), the stale record and ruling R15's protection each lack one owner and one test surface; producers mark stale and write to separate sensor and motor stores. One module should accept samples and feedback, age them against their freshness windows and hand out a coherent copy. Design settled with Lenton Neale on 2026-10-15 (architecture review, candidate 1).

## Scope

New `latest_value.[ch]` (prefix `LatestValue_`) replacing `sensor_latest_value` and `motor_latest_value`, with serialisation moving to `spi_protocol.c`. Not covered: escalation per PRM-MOT-02 (degraded, inhibit, FAULT), which stays in the CAN service.

## Acceptance Criteria

- [ ] `latest_value.[ch]` exists and is in both CMake source lists (`Arm_Sensor_Hub/CMakeLists.txt`, `tests/host/CMakeLists.txt`); the two old stores are gone
- [ ] The interface is Configure, AcceptSample, AcceptFeedback and CopySnapshot only; not-fitted and not-registered are slot properties set by Configure, and a write to such a slot returns an error
- [ ] Freshness is decided at CopySnapshot (stale when now minus acquisition timestamp exceeds the kind's window); the motor window is PRM-MOT-01, and a new Provisional register row sets the sensor window to 5 x PRM-ACQ-05 (100 ms), basis Derived, to be Measured in Stage 3
- [ ] Typed feedback is merged with per-field timestamps; the record is valid once a position has arrived; the raw last 31H reply and command code are kept only so the schema v1 motor record stays byte-identical (R10(a))
- [ ] Raw counts become millidegrees inside AcceptSample (scale only, calibration version 0); `synchronization_quality` and the TIMESTAMP_SYNCHRONIZED bit are removed (R16, wire bit written zero)
- [ ] CopySnapshot and every accept run in a FreeRTOS critical section, meeting R15's lock-or-double-buffer obligation; the store depends on no TimeService or HAL
- [ ] Snapshot serialisation moves from `spi_slave_service.c:146-228` to `spi_protocol.c` and reads the caller's copy; the SPI service copies on the PRM-ACQ-01 period and on every GET_SNAPSHOT into its own static buffer; the sensor task and CAN service only accept
- [ ] `protocol_test_main.c` feeds samples and feedback at chosen times, copies later and checks records, ageing, refused writes and the serialised bytes against the Python side; the old setter and staging tests are replaced
- [ ] `FIRMWARE_ARCHITECTURE.md` lists the module and the component documentation names the store as the implementation of section 8 coherency
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests in `protocol_test_main.c` and `service_test_main.c`; the stack check still passes (static buffer, no growth on any task stack).

## References

- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` section 8
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (PRM-ACQ-01, PRM-ACQ-05, PRM-MOT-01, PRM-MOT-02)
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (rulings R10, R15, R16)
- `Arm_Sensor_Hub/Documentation/FIRMWARE_ARCHITECTURE.md`
