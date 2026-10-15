Origin: backlog story B65 (WP10, "S10.1 GET_SNAPSHOT serves the latest sensor and motor records as a correlated SNAPSHOT")

## Context

The Pi cannot yet poll for the latest fitted-encoder readings: GET_SNAPSHOT is not answered with a SNAPSHOT correlated to the request (findings SPI-1, FW-1, PRM-8, VER-21). SYS-SPI-001 relies on polling for recovery and on correlated responses. The SNAPSHOT is built from the latest-value store's coherent copy.

## Scope

The STM32 reply path for GET_SNAPSHOT and its host test. Not covered: the Pi logger (a separate issue) and motor record content beyond the registered motors.

## Acceptance Criteria

- [ ] A GET_SNAPSHOT request is answered with a SNAPSHOT whose correlation fields match the request and which carries the six sensor records and the registered motor records
- [ ] The SNAPSHOT is serialised from a coherent copy taken at the time of the request, not from a previously staged frame
- [ ] A host test drives GET_SNAPSHOT through the service and checks the correlated reply
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests (`service_test_main.c`, `protocol_test_main.c`) and the Pi decode test; bench evidence belongs to the Stage 1 bench issue.

## References

- Review findings (evidence pointers): SPI-1, FW-1, PRM-8, VER-21
- Clauses: PRM-ACQ-01; SYS-ENC-001; SYS-ENC-001, SYS-SPI-001 ("polling ... provides recovery", "correlated GET_SNAPSHOT responses"); SYS-SPI-001
- Code and documents: `Arm_Sensor_Hub/App/Src/app_init.c:135-163`, `Arm_Sensor_Hub/App/Src/spi_protocol.c:172-178`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c:176-228;318-347;327-330;344-347`, `Arm_Sensor_Hub/Core/Src/main.c:441-456;441-457;447-455`, `Arm_Sensor_Hub/tests/host/service_test_main.c:1050-1096`, `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py:61-66`
- `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md`
