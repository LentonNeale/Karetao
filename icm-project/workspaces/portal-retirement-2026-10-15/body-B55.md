Origin: backlog story B55 (WP9, "S9.4 Shared golden-frame vectors asserted by the C and Python suites; contract constants named once per side")

## Context

The SPI frame format is implemented twice (`spi_protocol.c` and `spi_protocol.py`) and must stay in lockstep. SYS-SPI-001 requires the C and Python protocol tests to exchange the same frames bit-for-bit, but no vectors are shared, and the contract constants (magic, header length, maximum frame and similar) are repeated across files on each side. This can be closed before the arm is connected.

## Scope

Golden-frame vectors in `shared/test-vectors`, asserted by both suites, and each contract constant named once per side. Not covered: any change to protocol behaviour, and the Pi exchange session and its fake (a separate issue that builds on these vectors).

## Acceptance Criteria

- [ ] Golden vectors live in `shared/test-vectors` and are asserted byte for byte by both the C host tests and the Python tests
- [ ] The vectors include the 4-byte GET request (R1), a frame with non-zero bytes after the CRC (R4), the R18 reason codes, and the system-activate request and reply (R19b)
- [ ] Each contract constant at the cited locations is defined once per side and referenced elsewhere
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

C host tests (`ctest --preset HostTests`) and Python tests (`python -m unittest discover -s RaspberryPi_Sensor_Hub/tests/spi`) both pass against the same vector files.

## References

- Review findings (evidence pointers): SPI-10, VER-23, PRM-19, PRM-20
- Clauses: SPI section 14; SPI section 3; SYS-SPI-001 acceptance; SYS-SPI-001 acceptance ("the C and Python protocol tests exchange the same frames bit-for-bit")
- Code and documents: `Arm_Sensor_Hub/App/Inc/spi_protocol.h:25-27`, `Arm_Sensor_Hub/App/Src/spi_protocol.c:30`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c:204`, `Arm_Sensor_Hub/tests/host/CMakeLists.txt`, `Arm_Sensor_Hub/tests/host/protocol_test_main.c:613-652;613-726`, `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md:231`, `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py:40`, `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:34-49`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:34-40`, `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py:48-80`
