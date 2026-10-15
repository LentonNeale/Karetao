Origin: backlog story B68 (WP10, "S10.4 Pi snapshot logger and probe output for Stage 1 evidence")

## Context

There is no Pi-side logger that streams snapshots and files them with Pi receive times, so Stage 1 has no evidence source for fitted-encoder readings (findings SPI-6, HOST-3, VER-22). Measurement history is owned on the Pi (decision SD-09). The logger is a stream over the Pi `ExchangeSession`, one GET_SNAPSHOT per transaction, each reply correlated to the request before it.

## Scope

The logger module, the probe output in `spi_link_probe.py` and their tests. Not covered: motor-side content and the bench run itself.

## Acceptance Criteria

- [ ] The logger streams GET_SNAPSHOT at the registered period (PRM-ACQ-01)
- [ ] Duplicate snapshots are rejected
- [ ] Each record is filed with its Pi receive time
- [ ] The probe output is usable as Stage 1 evidence and `test_spi_link_probe.py` drives it end to end
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Pi tests against the firmware-rules fake: period, duplicate rejection, receive-time filing.

## References

- Review findings (evidence pointers): SPI-6, HOST-3, VER-22
- Clauses: HOST_SYSTEM_INTERFACE SD-09; SYS-ENC-001; SYS-SPI-001 acceptance
- Code and documents: `RaspberryPi_Sensor_Hub/src/spi/spi_device.py:25-97`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:189-244;220-229;64-100`, `RaspberryPi_Sensor_Hub/tests/spi/test_spi_link_probe.py:23-55`, `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py:166-201;61-76`
- `Documentation/02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md` (SD-09 measurement history)
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (PRM-ACQ-01)
