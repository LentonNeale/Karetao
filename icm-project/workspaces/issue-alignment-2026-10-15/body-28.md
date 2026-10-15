## Context

Implement the calibration-record half of `SYS-CAL-001`: a calibration record is valid only if it is versioned, CRC-checked and approved for use, and the active record is immutable while in use (`SYSTEM_CONFIGURATION.md` §3).

The other half of the original scope, calibration validity as a motion-gate prerequisite, is withdrawn by decision D-3 (`Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`, "Motion gate"): calibration validity is not a gate input for single gated commands. Ruling R26 defers this work to after Stage 4; gated motion uses raw shaft angles until then.

## Scope

- Document the ownership of approved and CRC-valid calibration status at the configuration boundary.
- Prevent calibration mutation while the lifecycle is ACTIVE.
- Require validation and explicit reactivation (SYS-REC-001) when replacing calibration.

Not in scope: any calibration input to the motion gate (D-3).

## Acceptance Criteria

- [ ] Ownership of approved and CRC-valid calibration status is documented at the configuration boundary.
- [ ] Calibration mutation while ACTIVE is rejected.
- [ ] Calibration replacement follows the validation and explicit reactivation sequence.

## Verification / Evidence

Unit and integration tests for CRC validity, active-state mutation rejection and replacement with revalidation. Evidence is recorded for the `SYS-CAL-001` row in `SYSTEM_VERIFICATION_MATRIX.md` and shared with #47.

## References

- `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` §3
- `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`: SYS-CAL-001 (SYS-CAL-002 is merged into it), SYS-REC-001
- `ARCHITECTURE_DECISIONS.md`: D-3, ruling R26
- Former parent LentonNeale/Karetao#10 is closed as superseded (LIVE-20)
