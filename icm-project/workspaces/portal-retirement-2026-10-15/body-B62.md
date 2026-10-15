Origin: backlog story B62 (WP9, "S9.11 Pi packaging and small defects: pyproject, shared ACK parser and sequencer, resource cleanup, stable spidev path, adapter tests")

## Context

The Pi package has no `pyproject`, the ACK parser and sequencer are duplicated, resources are not released on error, the spidev device path is not stable across bus renumbering, and the adapters lack tests (findings HOST-21 to HOST-25).

## Scope

Packaging and small defects in `RaspberryPi_Sensor_Hub/src/spi` and `tools`. The shared sequencer is the process-wide Sequencer built by the Pi exchange-session issue; this issue points at it and does not build a second one.

## Acceptance Criteria

- [ ] A `pyproject` makes the Pi package installable and the tests runnable from it
- [ ] There is one ACK parser and one sequencer, shared by the library and the tools
- [ ] SPI and GPIO resources are released on error paths, covered by tests
- [ ] The spidev path is stable across bus renumbering (see the linux-spidev bus-number note)
- [ ] The SPI adapters have unit tests
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Pi unit tests; installing from `pyproject` in a clean virtual environment runs the suite.

## References

- Review findings (evidence pointers): HOST-22, HOST-23, HOST-24, HOST-25, HOST-21
- Clauses: VERIFICATION_STRATEGY Chain; external: linux-spidev py-spidev-api Bus number stability; none (defect); none (duplication); none (maintainability)
- Code and documents: `RaspberryPi_Sensor_Hub/src/spi/data_ready.py:83-90`, `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py:39;66-68;66-72;87-95`, `RaspberryPi_Sensor_Hub/src/spi/spi_device.py:85-91`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:58-61`, `RaspberryPi_Sensor_Hub/tests/spi/`, `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py:6`, `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py:126-128;155-157;27`
- `Documentation/05_VERIFICATION/VERIFICATION_STRATEGY.md` (Chain)
- `icm-project/references/linux-spidev`
