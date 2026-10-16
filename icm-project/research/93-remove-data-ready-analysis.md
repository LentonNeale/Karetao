# Issue #93: Remove data_ready_analysis.py and its unbased verdicts

Date: 2026-10-16. Branch: `issue/93-remove-data-ready-analysis`. Requirement or ruling served: ruling R7 (settles findings HOST-20, VER-19, PRM-15); `DOCUMENTATION_RULES.md` Numbers.

## Mechanism

Explained layer by layer. From this issue on, no issue gets prediction questions (project `CLAUDE.md`, changed 2026-10-16). The first two layers were asked as predictions before that change; their answers are kept in the last column.

| Layer | What the source shows | Pointer | Prediction (before the change) |
|---|---|---|---|
| Ruling and numbers | SYS-SPI-004 is retired; its 20–30 cm moved to PRM-SPI-05, a length. The module's 5 ms is a time, so re-citing it to that row gives it no basis: no `PRM-*` row bounds DATA_READY→NSS latency. R7 removes the module rather than repairing it, and allows a replacement only after a register row exists. | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md:51`; `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md:47`; `Documentation/DOCUMENTATION_RULES.md` Numbers; `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md:111` | "Requirements can't hold numbers": partly held. That rule is why SYS-SPI-004 was retired, but re-citing still fails on units. |
| Contract | SPI §16 lists "DATA_READY electrical timing and Raspberry Pi GPIO behavior" as a Stage 3 measurement with no limit. It is a characterisation to record, not an acceptance criterion, so the module's "compliant" verdict had no pass mark to grade against. | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` §16 | "Says nothing about it": did not hold. |
| Code | `TimingSession._record()` never passes the three DATA_READY fields, so every record and every harness CSV row has them empty. The Pi is the SPI master and spidev drives chip-select inside the ioctl, so Python sees neither NSS edge; only the DATA_READY rise is visible, through gpiod. The analysis and its 17 tests ran over a column nothing writes; `data_ready_latency_ms()` read the same dead field. | `RaspberryPi_Sensor_Hub/src/spi/timing.py` `_record()`; `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py:346-350`; `RaspberryPi_Sensor_Hub/src/spi/data_ready.py:95-109` | not asked |
| Hardware | A signal in cable travels at roughly 0.6–0.7 c (about 5 ns/m), so 30 cm adds about 1.5 ns. The removed comment's "~5 µs per 30 cm", "~170 ns/meter" and 5 ms do not follow from each other or from that. DATA_READY→NSS is dominated by the Pi's software wake-up path (gpiod edge, process wake, encode, spidev ioctl), which is unmeasured. That is why R7 sends Stage 3 to the logic analyser (R17a) and the Pi edge timestamps (HOST-8). General transmission-line physics; `icm-project/references/` has no note for it. | removed `data_ready_analysis.py:7,89-90` | not asked |

## Concepts met

- **Dead field**: a schema slot no producer writes. Every consumer (analysis, tests, CSV column) then looks healthy while measuring nothing.
- **Characterisation versus acceptance criterion**: §16 asks Stage 3 to measure DATA_READY timing. Only a register row with a basis can turn that measurement into a pass/fail limit.
- **Dimensional consistency of a citation**: a number's basis must be a value of the same kind; a length row cannot justify a time limit.
- **Velocity factor**: signal speed in a cable as a fraction of c; it makes cable delay at bench lengths nanoseconds, not micro- or milliseconds.
- **SPI master owns chip-select**: on the Pi the kernel spidev driver asserts NSS, so user-space timing cannot see NSS edges; a logic analyser can.

## What the change did and how it was verified

Deleted `RaspberryPi_Sensor_Hub/src/spi/data_ready_analysis.py` (146 lines) and `RaspberryPi_Sensor_Hub/tests/spi/test_data_ready_analysis.py` (17 tests). Removed `data_ready_to_nss_low_us`, `nss_high_to_data_ready_low_us`, `data_ready_interval_us` and `data_ready_latency_ms()` from `TransactionRecord` in `timing.py`. `spi_timing_harness.py` CSVs lose three columns that were always empty; no committed file or tool reads them. `SYSTEM_VERIFICATION_MATRIX.md` row SYS-SPI-001 no longer names the deleted test as Pi evidence; the grep found that site, which the issue text did not list.

Checks on 2026-10-16 in the worktree: Pi tests 212 pass (229 before; the difference is exactly the 17 deleted tests); HostTests 6 of 6; Debug build passes with the stack check; `doc_check` clean. A grep for the module name, its functions and the three fields finds them only in R7 itself, the Portal-retirement workspace that created this issue, and the two as-built TIME_SYNC documents left to #45 (below).

`/code-review medium` found no correctness defect and four documentation leftovers. Two are the #45-owned sites below, cross-referenced in the pull request. `RaspberryPi_Sensor_Hub/Documentation/README.md` (SPI Timing Harness) said DATA_READY latency waited on a GPIO watcher that already exists; it now says the harness records the Pi-side wait (`data_ready_wait_ns`) and that DATA_READY-to-NSS timing is a Stage 3 logic-analyser measurement, matching the harness docstring. The local `.claude/CLAUDE.md` overview no longer lists data-ready analysis tools (untracked, so not in this diff). Rechecked after the fixes: Pi tests 212 pass, `doc_check` clean.

## Left on purpose (owned elsewhere)

- `RaspberryPi_Sensor_Hub/tests/spi/test_validation_claims.py` (`SYSSpi004CableTests`), `Documentation/05_VERIFICATION/TIME_SYNC_VALIDATION.md` (SYS-SPI-004 section and summary row, which still name `data_ready_analysis.py (future)` and the 5000 µs criterion) and `TIME_SYNC_CHARACTERISATION_EVIDENCE.md:198` still cite SYS-SPI-004. Issue #45 deletes all three by name (R16), so this issue reads its "no remaining file cites SYS-SPI-004" criterion as "no live citation outside #45's deletions". Decided by Lenton when confirming the plan.
- `SYSTEM_REQUIREMENTS.md:51`, `PARAMETER_REGISTER.md:47` and `CHARTER_ALIGNMENT_PLAN.md:337` name SYS-SPI-004 only as retired: traceability, kept.
- `RASPBERRY_PI_BRINGUP_V1.md:922` is the dated 2026-09-20 conflict-review appendix, a historical record.

## Open questions

- None.
