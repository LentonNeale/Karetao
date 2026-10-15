Origin: backlog story B73 (WP10, "S10.9 Sensor path hardening: fewer I2C transactions, bus recovery, bring-up retry, timeout diagnostics")

## Context

A stuck I2C bus, a failed bring-up and a timeout leave the sensor path with no recovery and little diagnostic detail (findings FW-11, FW-12, FW-13, FW-15, GATE-21). The 'fewer I2C transactions' item is covered by the AS5600 sample issue (two burst reads under one scoped lock); this issue keeps the rest.

## Scope

`i2c_manager.c`, `sensor_task.c`, `tca9548a_mux.c`, and the I2C timing in the `.ioc` if it changes (regenerate `Core/` headless). Not covered: the burst-read change.

## Acceptance Criteria

- [ ] The I2C manager recovers a stuck bus and reports the recovery
- [ ] Sensor bring-up retries and reports a persistent failure rather than failing once
- [ ] Timeouts produce diagnostics as `I2C_MANAGER_CONTRACT.md` (Diagnostics; Timeout and Error Policy) requires
- [ ] The recovery behaviour meets SYS-REC-001 and uses PRM-ACQ-03
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests with scripted I2C failures; the stack check passes.

## References

- Review findings (evidence pointers): FW-11, FW-12, FW-13, FW-15, GATE-21
- Clauses: I2C_MANAGER_CONTRACT Diagnostics; I2C_MANAGER_CONTRACT Timeout and Error Policy; PRM-ACQ-03; SYS-REC-001
- Code and documents: `Arm_Sensor_Hub/App/Src/app_init.c:144-148`, `Arm_Sensor_Hub/App/Src/as5600.c:36-61`, `Arm_Sensor_Hub/App/Src/i2c_manager.c:268-273;285-335;545-564;74-130`, `Arm_Sensor_Hub/App/Src/sensor_task.c:107-115;312-315;62-71;62-72`, `Arm_Sensor_Hub/App/Src/tca9548a_mux.c:92-125`, `Arm_Sensor_Hub/Arm_Sensor_Hub.ioc:55-71`
- `Arm_Sensor_Hub/Documentation/I2C_MANAGER_CONTRACT.md`
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (PRM-ACQ-03)
