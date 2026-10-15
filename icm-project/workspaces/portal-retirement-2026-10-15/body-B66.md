Origin: backlog story B66 (WP10, "S10.2 SPI service re-arm, stall and NSS-resync fixes with one source of truth for armed")

## Context

The SPI service can wedge after a frame is staged while one is armed, after a HAL arm failure, or after a stall-abort race, and a stall does not re-arm the same frame (findings SPI-2, SPI-13, SPI-16). When the service wedges the Pi gets no further replies. The armed state itself becomes the frame pool's DMA state in the response-path issue; this issue keeps the stall, re-arm and NSS-resync fixes.

## Scope

`spi_slave_service.c`, `spi_data_ready.c` and the NSS configuration in the `.ioc` if it changes (regenerate `Core/` headless; the diff must show only that change). Not covered: the DATA_READY assertion rule (a separate issue).

## Acceptance Criteria

- [ ] The service never wedges after stage-while-armed, a HAL arm failure, or a stall-abort race, each shown by a host test
- [ ] A stall re-arms the same frame
- [ ] The NSS-resync path recovers the transfer after a mid-frame NSS change
- [ ] There is one source of truth for armed: the frame pool's DMA state
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests in `service_test_main.c` for each failure path; no new task stack use (stack check passes).

## References

- Review findings (evidence pointers): SPI-2, SPI-13, SPI-16
- Clauses: SPI_SYSTEM_INTERFACE §16 Stage 3, §14; SPI_SYSTEM_INTERFACE §7; SPI_SYSTEM_INTERFACE §7, §8
- Code and documents: `Arm_Sensor_Hub/App/Src/spi_data_ready.c:20-44;38-44`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c:100-118;100-133;272-316;296-306;396-409`, `Arm_Sensor_Hub/Arm_Sensor_Hub.ioc:101-103`, `Arm_Sensor_Hub/Core/Src/main.c:301-329`
- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` sections 7, 8, 14 and 16 (Stage 3)
