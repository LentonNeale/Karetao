Origin: backlog story B67 (WP10, "S10.3 DATA_READY armed-then-assert on the STM32; fresh-edge wait and chip lookup fix on the Pi")

## Context

Contract rule C-1 says DATA_READY is high exactly while a frame is armed. Today `spi_data_ready.c` models high while staged and low once consumed into DMA, and the service writes the pin after the module has cleared its state, so the module's flag and the pin disagree while a frame is armed. On the Pi, the wait can return on a stale level and the chip lookup is wrong (findings SPI-3, HOST-7, HOST-8). Design 2026-10-15 (architecture review, candidate 5).

## Scope

`spi_data_ready.[ch]`, the service's use of it, and the Pi `data_ready.py`. Not covered: the armed-state fixes (a separate issue).

## Acceptance Criteria

- [ ] Ruling R8(a): DATA_READY is LOW whenever no frame is armed (C-1), asserted by a host test with a recording pin through stage, arm, complete and abort
- [ ] `SpiDataReady_Init` takes an injected pin setter and the stall timeout and poll period from PRM-SPI-03 and PRM-SPI-04, converted to microseconds once
- [ ] `SpiDataReady_Tick(armed, staged, now_us)` writes a level exactly equal to armed, keeps only the last level and the time it rose, returns a verdict (none, re-arm, abort), and counts assertions, poll recoveries and host stalls
- [ ] The service executes the verdicts and deletes `SetDataReadyPin`, `s_dma_start_tick`, its own stall branch and the OnFrameStaged/OnFrameConsumed ordering
- [ ] The Pi waits for a fresh edge rather than returning on a stale level, and the chip lookup is fixed
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

`protocol_test_main.c` with a recording pin checks the verdicts at the right instants; the DMA-loop test in `service_test_main.c` asserts the recorded pin follows the pool state end to end; Pi tests for the fresh-edge wait.

## References

- Review findings (evidence pointers): SPI-3, HOST-7, HOST-8
- Clauses: C-1; SPI_SYSTEM_INTERFACE §13; SPI_SYSTEM_INTERFACE §7 and §17 invariant 10
- Code and documents: `Arm_Sensor_Hub/App/Src/spi_slave_service.c:120-133;332-337;396-404`, `RaspberryPi_Sensor_Hub/src/spi/data_ready.py:58-64;95-109`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:179-182`
- `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` sections 7, 13 and 17 (invariant 10)
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (rulings R8, C-1)
- `icm-project/references/libgpiod-v1`
