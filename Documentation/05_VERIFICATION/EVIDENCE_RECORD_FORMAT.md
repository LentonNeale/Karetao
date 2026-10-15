# Evidence record format

## Purpose

One record per verification run, filed as `Documentation/05_VERIFICATION/evidence/<date>-<short-name>.md` and referenced from the Test or Evidence column of `SYSTEM_VERIFICATION_MATRIX.md`. A record states what was run, on which firmware and hardware, and what was observed.

## Required fields

| Field | Content |
|---|---|
| Date | Date of the run (YYYY-MM-DD) |
| Requirement IDs | The `SYS-*` rows the run is offered against |
| Firmware identity | `git_hash_abbrev` and `build_flags` bit 0 from the `VERSION` message; Pi commit hash and whether the Pi working tree was dirty (ruling R28(b)) |
| Hardware or rig | Which STM32 board, which axes populated, which motors, which cable |
| Procedure | The steps, or the tool command used |
| Result | Pass or fail with the numbers observed, and the `PRM-*` IDs they inform |
| Attachments | CSV, logs, photos |
| Accepted by and date | Lenton Neale, date |

## Rules

- A record whose `build_flags` dirty bit (bit 0) is set is recorded but cannot satisfy a matrix row.
- A record whose Pi working tree had uncommitted changes under `RaspberryPi_Sensor_Hub/` or `shared/` at run time is recorded but cannot satisfy a matrix row, exactly as the firmware dirty bit (ruling R28(b), `ARCHITECTURE_DECISIONS.md`). The Pi check is scoped like the firmware's (`Arm_Sensor_Hub/` and `shared/`), so an edit elsewhere in the repository does not disqualify a run.
- A result that changes a register basis (Provisional to Measured) is linked from the register's Source column in `PARAMETER_REGISTER.md`.
- Records are never edited after acceptance. A new run is a new record.

## Run directories

A capturing tool writes one directory per run, by convention named `<date>-<kind>-<name>`, holding `meta.json` and one CSV per series. The run directory is the source of every tool-drafted field of a record, so `meta.json` carries these mandatory fields (decided in GitHub #109, carried by #70):

| Field | Content |
|---|---|
| `schema_version` | The run-record schema version, 1 |
| `kind` | The kind of run (for example `spi-link`, `encoder-read`); with the optional `name`, it names the record |
| `rig` | The Hardware or rig field, as text |
| `informs` | The identifiers the run informs: `SYS-*` rows it is offered against, `LIVE-*` items, `PRM-*` register rows |
| `started` | Start time as ISO 8601 with its UTC offset; its date is the record's Date |
| `tool_command` | The capture command, argument by argument |
| `firmware` | From the `VERSION` message: `version`, `git_hash` (eight hex digits), `commit_epoch_secs`, `protocol_version`, `dirty` (bit 0); hash `00000000` and `dirty` true with a `warning` when it could not be read |
| `pi` | `commit` (full hash), `dirty`, `scope`; empty commit, `dirty` true and an `error` when git could not read the tree |
| `series` | One entry per CSV: `name`, `file`, `columns`, `rows` |

The Pi `dirty` flag is `git status --porcelain` limited to `RaspberryPi_Sensor_Hub/` and `shared/`, run at capture time: the mirror of the firmware's build-time check over `Arm_Sensor_Hub/` and `shared/`. `RaspberryPi_Sensor_Hub/src/spi/run_record.py` implements this section for the Pi writer and the PC reader, the same lockstep as `spi_protocol.py` implements the SPI contract, and changes with it.

## Drafting a record

A record is tool-drafted and human-completed (GitHub #70, decided in #109). `RaspberryPi_Sensor_Hub/tools/evidence_record.py <run directory> --file` drafts `evidence/<date>-<kind>-<name>.md` from `meta.json`: Date, Requirement IDs (the `SYS-*` entries of `informs`), Firmware identity, Hardware or rig, Procedure and Attachments, and a statement of whether the run may satisfy a matrix row under the rules above. Result and Accepted by and date are written by Lenton Neale. The tool never overwrites an existing record and, with `--require-clean`, refuses to draft from a run that cannot satisfy a row.

## Sources of attachments

Attachments stay in the run directory and the record links them by relative path. The Pi harness `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py` still writes a `*_metadata.json` next to its data, including `dirty_build` from the `VERSION` message; until it adopts the run-record format, attach that file and the data it describes. The other tools in `RaspberryPi_Sensor_Hub/tools/` can supply logs for their own runs.
