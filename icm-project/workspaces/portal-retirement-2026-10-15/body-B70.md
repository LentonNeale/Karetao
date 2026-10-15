Origin: backlog story B70 (WP10, "S10.6 GET request payload defined and validated; padding rule stated and applied on both sides")

## Context

The GET request payload and the handling of bytes after the CRC are not defined consistently: the C and Python sides differ, and the Python side rejects non-zero tails (findings SPI-12, SPI-23). Rulings R1 and R4 settle the rules. The R1 check is a validation step in `SpiProtocol_ProcessRequest`.

## Scope

`SPI_PAYLOAD_SCHEMA.md` and `SPI_SYSTEM_INTERFACE.md` section 3 wording, then both implementations and tests. Not covered: other message payloads.

## Acceptance Criteria

- [ ] Ruling R1: every GET payload is `schema_version` plus three reserved zero bytes; BAD_LENGTH for another length, BAD_MESSAGE for another schema or non-zero reserved bytes; one Pi constant
- [ ] Ruling R4: bytes after the CRC are zero on transmit and ignored on receive on both sides, and the Python non-zero-tail check is removed
- [ ] The rule is stated in the SPI documents and applied identically in `spi_protocol.c` and `spi_protocol.py`
- [ ] The R1 check is a validation step in `SpiProtocol_ProcessRequest`, tested in `protocol_test_main.c`
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

C and Python tests using the shared golden vectors for the 4-byte GET request and the non-zero tail frame.

## References

- Review findings (evidence pointers): SPI-12, SPI-23
- Clauses: SPI_PAYLOAD_SCHEMA GET and Command Requests; SPI_SYSTEM_INTERFACE §3
- Code and documents: `Arm_Sensor_Hub/App/Src/spi_protocol.c:125-157`, `Arm_Sensor_Hub/tests/host/protocol_test_main.c:661`, `RaspberryPi_Sensor_Hub/src/spi/spi_device.py:40-45`, `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:142-145`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:189`
- `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` (GET and Command Requests)
- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` section 3
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (rulings R1, R4)
