# Verification Strategy

## Authority

This document defines how Karetao verification is recorded. `SYSTEM_VERIFICATION_MATRIX.md` holds the status; component repositories hold component tests; Lenton Neale accepts.

## Chain

Requirement (`SYSTEM_REQUIREMENTS.md`) -> code module -> test (host test, Pi test or bench procedure) -> evidence record -> matrix row -> accepted by Lenton Neale.
Every matrix row names its code module and its test, or says "none yet (issue: LIVE-xx)".

## Status vocabulary

| Status | Meaning |
|---|---|
| OPEN | No accepted evidence at the scope the requirement states, or not implemented |
| COMPONENT_EVIDENCE | A component test or host-test run passes; not enough to close the row |
| SYSTEM_VERIFIED | An evidence record shows the requirement on the real rig and Lenton Neale has accepted it, with date |

## Rules

- Component or host-test evidence never sets SYSTEM_VERIFIED, however many tests pass.
- Dirty-build rule: a record whose `VERSION` `build_flags` dirty bit (bit 0) is set is filed but cannot satisfy a row.
- Records are not edited after acceptance; a new run is a new record.
- Record format: `EVIDENCE_RECORD_FORMAT.md`.
