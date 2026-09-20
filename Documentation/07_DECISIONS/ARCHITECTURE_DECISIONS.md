# Architecture Decisions

## Proposed motion-permission decision

**Status:** PROPOSED — not yet approved.

A system-level normal-motion permission gate is proposed above individual service readiness. The proposal aggregates CAN readiness, required I2C/sensor readiness, Raspberry Pi communication health, time synchronization validity, required timestamp/data freshness, system lifecycle/fault readiness, and an explicit global motion-inhibit state.

The proposed gate is:

MOTION_PERMITTED = CAN_ACTIVE AND REQUIRED_I2C_ACTIVE AND REQUIRED_SENSOR_DATA_VALID AND PI_COMMUNICATION_HEALTHY AND TIME_SYNC_VALID AND REQUIRED_TIMESTAMP_FRESHNESS AND SYSTEM_OPERATIONAL AND NO_ACTIVE_MOTION_INHIBIT

This proposal is intended to resolve the existing open motion-permission authority issue under SD-02/SD-23. It does not alter the approved SD-01–SD-25 decisions until accepted by the system decision authority.

Open parameters include the final owner/API, exact required sensor set, freshness thresholds, global inhibit sources/clear semantics, and the boundary between controlled stop, motor disable, and independent safety functions.

Architecture-level decisions are maintained in the **[Karetao Decisions, Questions, and Issues Register](KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md)** under the **Architecture Decisions** section.

This is a placeholder document created during the documentation refactoring. All substantive content is in the central register to maintain a single source of truth for all project decisions.

For specific architecture decisions, refer to:
- `KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` § Architecture Decisions (§6)
- System-level architecture: `01_SYSTEM/SYSTEM_ARCHITECTURE.md`
- System lifecycle: `01_SYSTEM/SYSTEM_LIFECYCLE.md`
- System requirements: `01_SYSTEM/SYSTEM_REQUIREMENTS.md`
