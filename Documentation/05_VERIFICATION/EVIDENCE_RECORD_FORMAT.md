# Evidence record format

## Purpose

One record per verification run, filed as `Documentation/05_VERIFICATION/evidence/<date>-<short-name>.md` and referenced from the Test or Evidence column of `SYSTEM_VERIFICATION_MATRIX.md`. A record states what was run, on which firmware and hardware, and what was observed.

## Required fields

| Field | Content |
|---|---|
| Date | Date of the run (YYYY-MM-DD) |
| Requirement IDs | The `SYS-*` rows the run is offered against |
| Firmware identity | `git_hash_abbrev` and `build_flags` bit 0 from the `VERSION` message; Pi commit hash |
| Hardware or rig | Which STM32 board, which axes populated, which motors, which cable |
| Procedure | The steps, or the tool command used |
| Result | Pass or fail with the numbers observed, and the `PRM-*` IDs they inform |
| Attachments | CSV, logs, photos |
| Accepted by and date | Lenton Neale, date |

## Rules

- A record whose `build_flags` dirty bit (bit 0) is set is recorded but cannot satisfy a matrix row.
- A result that changes a register basis (Provisional to Measured) is linked from the register's Source column in `PARAMETER_REGISTER.md`.
- Records are never edited after acceptance. A new run is a new record.

## Sources of attachments

The Pi harness `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py` writes a `*_metadata.json` next to its data, including `dirty_build` from the `VERSION` message. Attach that file and the data it describes. The other tools in `RaspberryPi_Sensor_Hub/tools/` can supply logs for their own runs.
