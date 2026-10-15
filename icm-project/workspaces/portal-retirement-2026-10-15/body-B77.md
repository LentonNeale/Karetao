Origin: backlog story B77 (WP10, "S10.13 ENCODER_BENCH_PROCEDURE covers SYS-ENC-002 and is linked from the index and matrix")

## Context

`Documentation/05_VERIFICATION/ENCODER_BENCH_PROCEDURE.md` does not cover SYS-ENC-002 (a NOT_FITTED axis) and is not linked from `00_INDEX.md` or the verification matrix (findings DOC-5, DOC-9). The procedure is what the Stage 1 bench issue follows.

## Scope

The procedure, `00_INDEX.md:18` and matrix rows 11 and 12. Not covered: running the procedure.

## Acceptance Criteria

- [ ] The procedure has steps and pass criteria for SYS-ENC-002
- [ ] `00_INDEX.md` links the procedure
- [ ] The matrix rows for SYS-ENC-001 and SYS-ENC-002 name the procedure
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

`icm-project/tools/doc_check` link check; review by Lenton Neale.

## References

- Review findings (evidence pointers): DOC-5, DOC-9
- Clauses: 00_INDEX map; SYS-ENC-002
- Code and documents: `Documentation/00_INDEX.md:18`, `Documentation/05_VERIFICATION/ENCODER_BENCH_PROCEDURE.md:5,21,32`, `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md:11;12`
- `Documentation/05_VERIFICATION/ENCODER_BENCH_PROCEDURE.md`
- `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`
