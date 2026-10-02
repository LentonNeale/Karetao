# Karetao project charter

Status: Agreed 2026-10-03
Owner: Lenton Neale
Role: Scope authority. Sets purpose, goal priority, non-goals and who decides. It does not define system requirements; those stay in SYSTEM_REQUIREMENTS.md. It does not set numeric values; those go in the parameter register with a basis (goal 3).

## Purpose

Karetao is a hobby-level robotic arm platform (STM32 sensor hub, MKS CAN servos, Raspberry Pi host), built and maintained by one person. It aims for good engineering practice (traceability, recorded decisions, evidence before done) at a size one person can keep up.

## Goals (in priority order)

1. Read every fitted joint encoder reliably. Encoders are commissioned as they are mounted. The commissioning table records which axes have one, and the snapshot marks unfitted axes as unfitted, not a fault. At least one joint is expected to have no encoder and rely on motor shaft feedback.
2. Read all six motor shaft positions over CAN into the snapshot, at rest and during motion, with coherent timestamps.
3. Measure the links before specifying them. SPI clock, CAN bitrate, sync skew, poll periods and loss behaviour go in a parameter register. Each value carries a basis: Measured, Datasheet, Derived or Provisional. Provisional means an engineering estimate not yet confirmed. Provisional values are working values, never requirements.
4. Confirm the X, Y and Z joints as verified motion. Record the initial test evidence, pass their commands through the firmware gate, and mark them verified in the SYSTEM_VERIFICATION_MATRIX. The other three joints follow once their hardware is confirmed.
5. Keep the trail intact: requirement, code, test evidence, SYSTEM_VERIFICATION_MATRIX, at a size one person can maintain.

## Non-goals

- No PL or SIL claim. Operation is attended, by the maintainer only. Safety behaviour is still designed and tested, but no rating is claimed.
- No ROS 2 integration for now (not never; the overview keeps a future note).
- No high-rate state estimator. The 500 Hz EKF is dropped.
- No differential end effector until the hardware exists.
- No Pi-side trajectory or motion planning. Single gated commands from the Pi are in scope.
- No calendar commitments. Milestones are stages, not dates.
- No numeric requirement without a stated basis.

## Who decides

Lenton Neale decides scope, priorities, requirement approval and verification acceptance for Karetao. Where other documents refer to the "CTO" or the "system decision authority", that means Lenton Neale. Decisions already recorded as approved (SD-01 to SD-25, 2026-09-07) keep their status. Items marked proposed or open stay non-normative until he approves them.

## Related documents

- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md): still names the EKF and ROS 2 as core responsibilities. For scope this charter takes precedence, and the overview will be updated in the documentation pruning run.
- [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md): owns system requirements.
- [SYSTEM_VERIFICATION_MATRIX.md](../05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md): owns verification status (goals 4 and 5).
- [00_INDEX.md](../00_INDEX.md): entry point.
