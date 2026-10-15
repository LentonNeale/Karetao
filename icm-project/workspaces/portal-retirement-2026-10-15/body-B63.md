Origin: backlog story B63 (WP9, "S9.12 doc_check extensions: matrix trace, retired IDs, section references, index coverage, Used-by, commissioning table")

## Context

`doc_check` checks forbidden terms, links, numbers and `PRM-*` references, but not whether every matrix row traces to evidence, whether retired IDs are still cited, whether section references resolve, whether every document is indexed, whether `Used-by` lines are true, or whether the commissioning table in `app_init.c` agrees with `SYSTEM_CONFIGURATION.md` (findings VER-51, VER-54, DOC-41).

## Scope

`icm-project/tools/doc_check/` and its allow list. Not covered: fixing every finding the new checks raise outside the files named here (raise them as follow-up issues).

## Acceptance Criteria

- [ ] `doc_check` reports a matrix row with no trace, a cited retired ID, an unresolved section reference, a document missing from the index, and a false `Used-by`
- [ ] `doc_check` compares the commissioning table in `app_init.c:26-73` with `SYSTEM_CONFIGURATION.md` and reports a difference
- [ ] Each new check has a passing and a failing fixture
- [ ] Each finding is resolved as its report proposes, or a ruling by Lenton Neale records why not
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

`icm-project/tools/doc_check` run on the branch is clean, and its own tests cover each new check.

## References

- Review findings (evidence pointers): VER-51, VER-54, DOC-41
- Clauses: DOCUMENTATION_RULES check tool; SYS-ENC-003 ("checked by inspection; `VERIFICATION_STRATEGY.md` "Chain"
- Code and documents: `Arm_Sensor_Hub/App/Src/app_init.c:26-73`, `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md`, `icm-project/tools/doc_check/allowed.toml`, `icm-project/tools/doc_check/doc_check.py:26-36,41-46;89-155`
- `Documentation/DOCUMENTATION_RULES.md` (check tool)
