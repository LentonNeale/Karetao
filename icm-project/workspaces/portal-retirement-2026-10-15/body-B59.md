Origin: backlog story B59 (WP9, "S9.8 Remove dead Pi tests and the TIME_SYNC echo decoder; move sensor tests to their own class")

## Context

`test_validation_claims.py` and parts of `test_spi_protocol.py` cite retired requirements (SYS-SYNC-002 to 005, SYS-SPI-003/004, SYS-TIM-003) and check nothing in the baseline. The TIME_SYNC echo decoder in `spi_protocol.py` and `spi_protocol.c` is dead (findings VER-16, VER-17, HOST-19, SPI-18). ACK/NACK are 12 bytes per `SPI_PAYLOAD_SCHEMA.md`.

## Scope

Delete the dead tests and decoder, and move the sensor tests into their own test class. Not covered: removing TIME_SYNC itself (a lockstep issue in the Stage 2 milestone).

## Acceptance Criteria

- [ ] The dead Pi tests are removed and no retired requirement ID is cited by a remaining test
- [ ] The TIME_SYNC echo decoder is removed from the Python and C protocol modules, and the two stay in lockstep
- [ ] The sensor tests live in their own test class
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Test counts before and after are stated in the pull request, with each removed test justified.

## References

- Review findings (evidence pointers): VER-16, VER-17, HOST-19, SPI-18
- Clauses: SPI_PAYLOAD_SCHEMA ACK/NACK; `SPI_PAYLOAD_SCHEMA.md` "ACK (0x80) and NACK (0x81)" (12 bytes); none in the baseline. It cites retired SYS-SYNC-002..005, SYS-SPI-003/004, SYS-TIM-003.
- Code and documents: `Arm_Sensor_Hub/App/Src/spi_protocol.c:48-56`, `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:338-366`, `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py:201-266;268-317`, `RaspberryPi_Sensor_Hub/tests/spi/test_validation_claims.py:1-466`
