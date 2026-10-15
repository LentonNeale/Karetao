Origin: backlog story B57 (WP9, "S9.6 Evidence-record tool and 05_VERIFICATION/evidence/ with VERSION identity and Pi commit")

## Context

`Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md` defines the required fields of an evidence record, but no tool writes one and `Documentation/05_VERIFICATION/evidence/` does not exist (findings VER-40, HOST-11). Without it, bench runs cannot be tied to the exact firmware and Pi code that produced them. The build-time firmware identity it reads has already been merged.

## Scope

A Pi-side tool that writes one record per run into `Documentation/05_VERIFICATION/evidence/`. Not covered: running any bench procedure, and marking a matrix row `SYSTEM_VERIFIED` (only the Karetao process and the verification matrix do that).

## Acceptance Criteria

- [ ] The tool writes one record per run with every field under "Required fields" in `EVIDENCE_RECORD_FORMAT.md`
- [ ] Each record carries the firmware VERSION identity read from the device and the Pi git commit
- [ ] Ruling R28(b): a dirty Pi working tree disqualifies a record exactly as the firmware dirty bit does, and the tool refuses to mark it as satisfying a matrix row
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Pi unit tests cover a clean tree, a dirty tree and a missing field; one sample record is produced from the fake backend.

## References

- Review findings (evidence pointers): VER-40, HOST-11
- Clauses: EVIDENCE_RECORD_FORMAT Required fields; `EVIDENCE_RECORD_FORMAT.md` "Required fields"
- Code and documents: `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md:60`, `RaspberryPi_Sensor_Hub/tools/spi_link_probe.py:134-228`, `RaspberryPi_Sensor_Hub/tools/spi_timing_harness.py:281-335`
- `Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md`
