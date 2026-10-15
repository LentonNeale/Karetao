Origin: backlog story B71 (WP10, "S10.7 Snapshot flags bit and transport counters reported")

## Context

The snapshot flags field and the transport counters are not reported, so the Pi cannot tell that an unread snapshot was replaced or dropped (findings SPI-15, SPI-14). Ruling R5 defines the bit.

## Scope

`snapshot_builder.c`, `spi_slave_service.c`, `health_monitor.c` and the Pi decode. Not covered: counters for other message types.

## Acceptance Criteria

- [ ] Ruling R5: flags bit 0 is set when an unread snapshot was replaced or dropped
- [ ] `dropped_snapshot_count_low` counts snapshot drops and replacements only
- [ ] The transport counters named in section 8 of `SPI_SYSTEM_INTERFACE.md` are reported
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

C host test replacing an unread snapshot and checking bit 0 and the count; Pi decode test.

## References

- Review findings (evidence pointers): SPI-15, SPI-14
- Clauses: SPI_SYSTEM_INTERFACE §7, §8, §14; SPI_SYSTEM_INTERFACE §8
- Code and documents: `Arm_Sensor_Hub/App/Src/health_monitor.c:119`, `Arm_Sensor_Hub/App/Src/snapshot_builder.c:58;75;89`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c:208-209;341;406-409`
- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` sections 7, 8 and 14
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (ruling R5)
