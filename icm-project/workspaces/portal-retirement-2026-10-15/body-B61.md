Origin: backlog story B61 (WP9, "S9.10 One firmware parameter header and one Pi config module mirroring the register; CubeMX values checked at init")

## Context

Register values are repeated as literals across firmware and Pi code (findings PRM-24, PRM-25, PRM-18, HOST-16, PRM-17, PRM-14), and values owned by CubeMX are not checked against what the code expects. `PARAMETER_REGISTER.md` is the authority for numbers; code carries defaults that mirror it.

## Scope

One header under `Arm_Sensor_Hub/App/Inc` and one module under `RaspberryPi_Sensor_Hub/src`, each citing its `PRM-*` row, plus an init-time check of the CubeMX-owned values. Not covered: choosing or changing any value (the register decides).

## Acceptance Criteria

- [ ] One firmware parameter header holds every register-backed default, each with its `PRM-*` row cited, and the scattered literals at the cited locations use it
- [ ] One Pi config module mirrors the same rows, and the Pi code reads values from it
- [ ] CubeMX-owned values (`main.c:241-245`, `main.c:278`, `main.c:352`) are checked against the header at init, and a mismatch is reported
- [ ] The header and module mirror the new Provisional register rows as they land
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

A host test fails when a header value differs from its register row; the init check is covered by a host test with a mismatched value.

## References

- Review findings (evidence pointers): PRM-24, PRM-25, PRM-18, HOST-16, PRM-17, PRM-14
- Clauses: CHARTER_ALIGNMENT_PLAN section 11 item 9; PARAMETER_REGISTER role and code-default rule; PRM-CAN-01; PRM-SPI-01; PRM-SPI-04; SPI section 8
- Code and documents: `Arm_Sensor_Hub/App/Inc/sensor_task.h:21`, `Arm_Sensor_Hub/App/Inc/spi_payload_layout.h:87`, `Arm_Sensor_Hub/App/Src/can_service.c:37-38`, `Arm_Sensor_Hub/App/Src/can_tx_policy.c:11-13`, `Arm_Sensor_Hub/App/Src/sensor_task.c:14`, `Arm_Sensor_Hub/App/Src/spi_slave_service.c:141;40-41`, `Arm_Sensor_Hub/App/Src/tca9548a_mux.c:83`, `Arm_Sensor_Hub/Core/Src/main.c:241-245;278;352`, `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/src/mks_api.cpp:37`
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (role and code-default rule)
- `Documentation/CHARTER_ALIGNMENT_PLAN.md` section 11 item 9
