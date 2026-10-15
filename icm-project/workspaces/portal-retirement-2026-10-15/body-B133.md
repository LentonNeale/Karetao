Origin: backlog story B133 (WP10, "S10.17 AS5600 sample in two transactions: burst reads under one scoped I2C lock, repeated-start write-read, typed magnet condition; driver interface down to InitDevice and ReadSample")

## Context

One joint-encoder sample costs fifteen bus transactions, which sets the sweep time (PRM-ACQ-02, 46 ms measured). The AS5600 address pointer increments after each byte except that ANGLE, RAW ANGLE and MAGNITUDE suppress the increment on reads, so a 3-byte read at 0x0B yields STATUS and RAW ANGLE and a 3-byte read at 0x1A yields AGC and MAGNITUDE. Design settled with Lenton Neale on 2026-10-15 after the datasheet check (architecture review, candidate 6).

## Scope

`as5600.[ch]`, the I2C manager's scoped lock and write-read primitive, and the HAL stub. Not covered: reading AGC and MAGNITUDE every Nth sweep (a Stage 3 decision taken with a measurement).

## Acceptance Criteria

- [ ] `AS5600_ReadSample` takes the I2C manager's scoped lock, selects the mux channel only if the cached mask differs, reads 3 bytes at 0x0B, takes the acquisition timestamp immediately after, reads 3 bytes at 0x1A, and releases the lock: three bus transactions per axis, four on a cache miss
- [ ] The sample carries raw angle counts, status, AGC, magnitude, timestamp and a typed magnet condition (detected, missing, weak, strong) derived in the driver from MD, ML and MH; the sensor task holds no datasheet bits or record policy
- [ ] `as5600.h` shrinks to `AS5600_InitDevice`, `AS5600_ReadSample` and the magnet-condition type; the per-register readers and `RawToDegrees` are deleted and bring-up uses ReadSample
- [ ] The write-read primitive uses `HAL_I2C_Mem_Read` (repeated start) instead of Master_Transmit then Master_Receive with a STOP between; the manager's interface is otherwise unchanged
- [ ] `service_test_main.c` scripts per fitted axis: lock, mux write only on a cache miss, Mem_Read 3 bytes at 0x0B, Mem_Read 3 bytes at 0x1A, unlock, with the timestamp between the reads; existing bring-up, mux-map and not-fitted tests follow the new sequence
- [ ] `protocol_test_main.c` checks that the store maps each magnet condition to the R6 validity flags
- [ ] After it lands, PRM-ACQ-02 is re-measured with the sweep counter, the row stays Measured with the new date and value, and PRM-ACQ-01 is revisited against it
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests against the HAL stub (which gains `HAL_I2C_Mem_Read` and a lock counter); re-measurement over SWD recorded in the register row.

## References

- `icm-project/references/as5600/i2c-interface.md` (pages 15 and 19 of the local datasheet copy)
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (PRM-ACQ-01, PRM-ACQ-02)
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (ruling R6)
- `Arm_Sensor_Hub/Documentation/I2C_MANAGER_CONTRACT.md`
