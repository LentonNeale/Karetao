Origin: backlog story B69 (WP10, "S10.5 Sequence seeding across processes and a host resync rule")

## Context

A second Pi process that starts from the same sequence seed is locked out by the STM32's high-water mark (findings HOST-9, SPI-21). Ruling R3 settles the rule: after a DIAGNOSTIC the STM32 accepts the first sequence and sets its mark from it.

## Scope

The firmware's first-sequence acceptance and the Pi Sequencer's bounded jump. Not covered: the Sequencer's construction, which belongs to the Pi exchange-session issue.

## Acceptance Criteria

- [ ] After a DIAGNOSTIC the STM32 accepts the first sequence received and sets its high-water mark from it (R3)
- [ ] One process-wide Pi sequencer with no stride supplies sequences
- [ ] On BAD_SEQUENCE to its first request the Pi jumps forward once by a bounded step and reports the jump
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

C host test for first-sequence acceptance after a DIAGNOSTIC; Pi test for the single bounded jump through the fake.

## References

- Review findings (evidence pointers): HOST-9, SPI-21
- Clauses: SPI_SYSTEM_INTERFACE §6; SPI_SYSTEM_INTERFACE §6, §14
- Code and documents: `Arm_Sensor_Hub/App/Src/spi_protocol.c:145-147;24`, `RaspberryPi_Sensor_Hub/src/spi/spi_device.py:28`, `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:59-102;65;68-97`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:154`, `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py:303`
- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` sections 6 and 14
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (ruling R3)
