## Context

Complete integrated system verification and establish the evidence required before `SYSTEM_VERIFIED` can be assigned. The charter removed the "release conditions" framing: `SYSTEM_VERIFIED` is simply a row accepted by Lenton Neale in `SYSTEM_VERIFICATION_MATRIX.md`, which only the Karetao process can set. Component test evidence does not count.

## Scope

Bring the matrix rows for the charter goals to accepted evidence. This issue is the handle for register item LIVE-09; the per-stage evidence is collected by the stage verification issues (#67, #62, #32, #65).

## Acceptance Criteria

- [ ] Every matrix row for the charter goals has an evidence record accepted by Lenton Neale.
- [ ] Each record carries the `VERSION` identity from a clean build.
- [ ] The matrix records the system as verified only when the required evidence is complete.

## Verification / Evidence

`Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` and `EVIDENCE_RECORD_FORMAT.md`.

## References

- `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` LIVE-09
- `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`; `Documentation/05_VERIFICATION/VERIFICATION_STRATEGY.md`
