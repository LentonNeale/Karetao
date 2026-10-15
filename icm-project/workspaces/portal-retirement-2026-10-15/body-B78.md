Origin: backlog story B78 (WP10, "S10.14 Retire or repurpose data_ready_analysis and its unbased verdicts")

## Context

`data_ready_analysis.py` cites a retired requirement (SYS-SPI-004) and applies a 5 ms bound with no register row (findings HOST-20, VER-19, PRM-15). Numbers need a basis in `PARAMETER_REGISTER.md` (`DOCUMENTATION_RULES.md`, Numbers).

## Scope

Ruling R7: remove the module, its tests and the three dead `TransactionRecord` fields. Not covered: a replacement analysis, which would need a register row first.

## Acceptance Criteria

- [ ] `data_ready_analysis.py` and `test_data_ready_analysis.py` are removed
- [ ] The three dead `TransactionRecord` fields are removed and no caller breaks
- [ ] No remaining file cites SYS-SPI-004 or the 5 ms bound
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Pi tests pass with the removed module's tests gone; a grep for the module name finds no reference.

## References

- Review findings (evidence pointers): HOST-20, VER-19, PRM-15
- Clauses: DOCUMENTATION_RULES Numbers; SPI_SYSTEM_INTERFACE §16; none in the baseline. It cites retired SYS-SPI-004, and its 5 ms bound has no PRM row.
- Code and documents: `RaspberryPi_Sensor_Hub/src/spi/data_ready_analysis.py:1-146;7;90;96`, `RaspberryPi_Sensor_Hub/src/spi/timing.py:98-100`, `RaspberryPi_Sensor_Hub/tests/spi/test_data_ready_analysis.py`
- `Documentation/DOCUMENTATION_RULES.md` (Numbers)
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (ruling R7)
