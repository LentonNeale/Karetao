# Documentation Framework Implementation Checklist

## Branch

- [ ] Repository is `LentonNeale/Karetao`.
- [ ] New branch created from `main`.
- [ ] Suggested branch name: `doc/documentation-framework`.
- [ ] No changes made to component repositories.

## Framework

- [ ] `Documentation/00_INDEX.md` created.
- [ ] `Documentation/01_SYSTEM/` created.
- [ ] `Documentation/02_INTERFACES/` created.
- [ ] `Documentation/03_COMPONENTS/` created.
- [ ] `Documentation/04_SAFETY/` created.
- [ ] `Documentation/05_VERIFICATION/` created.
- [ ] `Documentation/06_CONFIGURATION/` created.
- [ ] `Documentation/07_DECISIONS/` created.
- [ ] `Documentation/99_ARCHIVE/` created.

## Authority

- [ ] System authority explicitly assigned to Karetao.
- [ ] Arm Sensor Hub implementation authority assigned to `Arm_Sensor_Hub`.
- [ ] Raspberry Sensor Hub implementation authority assigned to `Raspberry_Sensor_Hub`.
- [ ] External/vendor authority explicitly distinguished.
- [ ] Verification evidence distinguished from requirements.

## Component Integration

- [ ] `COMPONENT_DOCUMENTATION_MODEL.md` created.
- [ ] Component repository documentation template defined.
- [ ] Component authority declaration defined.
- [ ] System requirement reference convention defined.
- [ ] System interface vs component implementation distinction defined.
- [ ] Verification relationship defined.
- [ ] Archive/supersession rules defined.

## Refactor State

- [x] Framework established.
- [x] Audit-derived system documentation reconciliation underway.
- [ ] Legacy documentation fully reconciled and superseded where appropriate.
- [ ] Final link and authority validation complete.

## Scope Control

- [x] Component repositories remain unchanged by this refactor.
- [x] Archived `docs/project/archive/**` content is excluded from current migration.
- [ ] Legacy documents are only superseded after authoritative content and provenance are established.
- [ ] Arm Sensor Hub documentation has not been copied.
- [ ] Raspberry Sensor Hub documentation has not been copied.
- [ ] Source code unchanged.
- [ ] Tests unchanged.
- [ ] Generated files unchanged.
- [ ] Submodules unchanged.

## Review

The branch is ready for review when a reviewer can answer:

> Where does each category of system-level documentation belong?

and:

> How should a component repository document its implementation without creating a competing system authority?
