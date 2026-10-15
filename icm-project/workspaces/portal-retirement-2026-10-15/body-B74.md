Origin: backlog story B74 (WP10, "S10.10 Sensor policy rulings applied: magnet warnings, processed-angle source, sweep measurement counter")

## Context

Three sensor policy rulings are not applied (findings FW-17, FW-18, FW-10). Ruling R6 settles them. The processed angle is computed in the latest-value store from RAW ANGLE, and the ANGLE register is no longer read.

## Scope

The policy in the latest-value store, `sensor_task.c`, the PRM-ACQ-02 register note and the TIM2 sweep counter. The sweep counter is the instrument for re-measuring PRM-ACQ-02 after the AS5600 sample issue lands.

## Acceptance Criteria

- [ ] Ruling R6: ML and MH are warnings and SAMPLE_VALID stays set
- [ ] `processed_angle_mdeg = RAW ANGLE x 360000 / 4096`, computed in the latest-value store's AcceptSample
- [ ] The PRM-ACQ-02 note reads 'method not recorded; believed to include the unpopulated channel' and records that it was measured on a Debug build, values read over the debug terminal (Lenton Neale, 2026-10-15); the Stage 3 re-measurement names the build type
- [ ] A TIM2 sweep counter is readable over SWD
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests for the magnet-condition to validity-flag mapping; the counter is read over SWD per `SWD_READOUT_PROCEDURES.md`.

## References

- Review findings (evidence pointers): FW-17, FW-18, FW-10
- Clauses: PRM-ACQ-02; SPI_PAYLOAD_SCHEMA validity flags; SYSTEM_CONFIGURATION §5
- Code and documents: `Arm_Sensor_Hub/App/Src/as5600.c:101-125;199-241`, `Arm_Sensor_Hub/App/Src/i2c_manager.c:375-417`, `Arm_Sensor_Hub/App/Src/sensor_task.c:154-173;177-185`, `Arm_Sensor_Hub/tools/check-sensors.sh:97-130`
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (ruling R6)
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (PRM-ACQ-02)
- `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` section 5
- `Arm_Sensor_Hub/Documentation/SWD_READOUT_PROCEDURES.md`
