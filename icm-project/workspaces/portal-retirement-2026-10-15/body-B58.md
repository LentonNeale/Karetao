Origin: backlog story B58 (WP9, "S9.7 Host-test harness: NDEBUG guard, CAN TX log, deeper I2C scripts, real time_service in service tests")

## Context

Four defects in the host-test harness (findings VER-34 to VER-37) let tests pass without checking what they claim: asserts can be compiled out under `NDEBUG`, there is no record of CAN frames sent (frame order matters: stop, then disable, SAFE-04), the I2C scripts are shallow, and the service tests use a stub instead of the real `time_service` (Issue #12 ISR capture).

## Scope

Harness changes under `Arm_Sensor_Hub/tests/host/` and the CMake/preset settings they need. Not covered: new product behaviour.

## Acceptance Criteria

- [ ] The host tests fail to build or run if `NDEBUG` is defined, so asserts cannot be silently removed
- [ ] A CAN transmit log records every frame sent, and a test asserts stop is sent before disable
- [ ] The I2C scripts are deep enough to check the sequence of reads and writes per transaction
- [ ] The service tests link the real `time_service.c` (`TIME_SERVICE_HOST_TEST`) instead of a stub
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

`ctest --preset HostTests` passes, and a deliberately broken frame order makes the new test fail.

## References

- Review findings (evidence pointers): VER-34, VER-35, VER-36, VER-37
- Clauses: SYS-ENC-001; SYS-LINK-002, SYS-CMD-001, SAFE-04 (frame order matters: stop, then disable); SYS-SYNC-001, SYS-TS-001 (Issue #12 ISR capture); none (defect in the test harness)
- Code and documents: `Arm_Sensor_Hub/App/Src/time_service.c:10-27,330-388`, `Arm_Sensor_Hub/CMakeLists.txt:20-22`, `Arm_Sensor_Hub/CMakePresets.json:84-91`, `Arm_Sensor_Hub/tests/host/CMakeLists.txt:27-56`, `Arm_Sensor_Hub/tests/host/protocol_test_main.c:1`, `Arm_Sensor_Hub/tests/host/service_test_main.c:156-203,951-956;57-64,254-279;84-86,359-376`, `service_test_main.c:1`
