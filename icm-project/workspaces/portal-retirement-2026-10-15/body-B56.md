Origin: backlog story B56 (WP9, "S9.5 Restore the MksServo codec host tests and check them against the MKS manual")

## Context

The MksServo C++17 library has no working codec host tests (findings CAN-26, VER-24), so position decode and the stop and disable frames are not checked against the vendor manual. `CLAUDE.md` requires host tests for App modules; the library's own CMake and the host test CMake need to build and run them.

## Scope

Restore the codec host tests and check their expected bytes against the MKS manual. Not covered: new drive commands or the drive-protocol module.

## Acceptance Criteria

- [ ] The MksServo codec host tests build and run under the `HostTests` preset
- [ ] Position decode (SYS-MOT-001) and the stop and disable frames (SYS-CMD-001, SYS-LINK-002) are asserted against byte values taken from the MKS manual, with the manual page cited in the test
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

`ctest --preset HostTests --output-on-failure` lists and passes the codec tests.

## References

- Review findings (evidence pointers): CAN-26, VER-24
- Clauses: CLAUDE.md host-test rule; SYS-MOT-001 (position decode), SYS-CMD-001, SYS-LINK-002 (stop and disable frames)
- Code and documents: `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/CMakeLists.txt:30-32;7,30-33`, `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/README.md:25`, `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/src/*.cpp`, `Arm_Sensor_Hub/tests/host/CMakeLists.txt:27-52`, `Arm_Sensor_Hub/tests/host/service_test_main.c:460-566;460-567`
- `icm-project/references/mks-servo42d-57d-can` (vendor manual extract; external authority)
