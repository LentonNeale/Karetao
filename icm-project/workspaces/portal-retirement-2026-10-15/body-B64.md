Origin: backlog story B64 (WP9, "S9.13 Remove dead and duplicated firmware code, including the ISR mutex-give async I2C path")

## Context

The firmware carries dead and duplicated code, including an async I2C path that gives a mutex from an ISR (findings FW-29, FW-14). Dead code hides real behaviour and an ISR mutex give is a defect if ever reached.

## Scope

Removal at the cited locations only. Changes under `Core/` go through the `.ioc` and headless regeneration, never by hand (`CLAUDE.md`). Not covered: behaviour changes.

## Acceptance Criteria

- [ ] The ISR mutex-give async I2C path is removed from `i2c_manager.c`, with no remaining caller
- [ ] The dead and duplicated code at the cited locations is removed, and a grep for each removed symbol finds none
- [ ] Any change to CubeMX output is made by editing the `.ioc` and regenerating, and the regenerated diff contains only that change
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Debug and Release builds pass, the stack check still passes, and the host tests are unchanged in count.

## References

- Review findings (evidence pointers): FW-29, FW-14
- Clauses: none (defect); none (tidiness)
- Code and documents: `Arm_Sensor_Hub/App/Src/as5600.c:243-246`, `Arm_Sensor_Hub/App/Src/i2c_manager.c:311-505;419-474;507-582`, `Arm_Sensor_Hub/App/Src/sensor_latest_value.c:112-121`, `Arm_Sensor_Hub/App/Src/spi_protocol.c:9-20`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c:54-86`, `Arm_Sensor_Hub/App/Src/tca9548a_mux.c:19-135`, `Arm_Sensor_Hub/Core/Src/stm32f4xx_hal_msp.c:179-186`
