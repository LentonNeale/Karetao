# Architecture Decisions

## Authority

This document is the Karetao destination for long-lived system and architecture decisions. Legacy SD records remain provenance for the decisions reconciled into current system requirements.

## Reconciled decisions

- **SD-01 — System timing:** 100 Hz baseline; current EKF setting 500 Hz; SPI initial maximum 5 MHz, with validation caveats.
- **SD-02 — Failure classification:** four response levels; motion-inhibit ownership requires explicit definition.
- **SD-03 — Raspberry communication loss:** 500 ms heartbeat timeout; reject motion; controlled stop where possible; motor disable; no last-command hold.
- **SD-04 — Feedback timeout:** five commissioned periods; escalation after three consecutive misses.
- **SD-05 — CAN requirements:** 1 Mbps, standard 11-bit IDs, load target, with hardware validation dependencies.
- **SD-06 — CAN failure:** bus-off inhibits commands, bounded recovery, escalation and explicit reactivation.
- **SD-07 — Joint/motor mapping:** deterministic versioned mapping including calibration terms.
- **SD-08 — Temporal alignment:** skew targets and acquisition timestamps.
- **SD-09 — Measurement history:** Raspberry/EKF owns history; STM32 supplies bounded latest-value/coherent records.
- **SD-10 — Calibration ownership:** Pi/workstation computes calibration; controlled transfer to STM32.
- **SD-11 — Calibration storage:** versioned, CRC-protected redundant flash storage with host source copy.
- **SD-12 — Angle representation:** calibrated radians authoritative at host/API; wire changes versioned.
- **SD-13 — Required joint state:** identity, state values, validity/status, timestamp, sync quality and calibration version.
- **SD-14 — Required command interface:** position/velocity, enable/disable/controlled-stop plus required gating.
- **SD-15 — Fixed SPI transaction:** 512-byte frame, 490-byte maximum payload, Mode 0, little-endian, CRC-32/ISO-HDLC.
- **SD-16 — GET_SNAPSHOT priority:** correlated response priority, immutable active DMA buffers, replace-if-new.
- **SD-17 — SPI host strategy:** DATA_READY plus 1 ms initial polling recovery; Pi is master.
- **SD-18 — Timestamp accuracy:** ≤ ±1 ms target and validity/age exposure.
- **SD-19 — TIME_SYNC frequency:** 1 Hz nominal, configurable to 10 Hz, five-second invalidation.
- **SD-20 — Loss of synchronization:** continue acquisition/diagnostics; inhibit time-dependent motion.
- **SD-21 — Time offset validation:** reject implausible updates without silent slew.
- **SD-22 — Reset time behaviour:** clear sync state; remain unsynchronized until accepted update.
- **SD-23 — Fault recovery:** bounded retries; persistent faults enter ERROR and recover to INACTIVE.
- **SD-24 — Restart/recovery:** dependency-ordered reactivation; never automatically resume motor motion.
- **SD-25 — Independent safety:** independent E-stop and safety mechanisms are release gates; boundary follows risk assessment.
- **SD-26 — Differential end-effector:** explicit motor-to-DOF mapping; proposed pending mechanical verification.

## Provenance rule

These entries preserve the SD identifiers as decision provenance. The authoritative requirement wording is in `01_SYSTEM/SYSTEM_REQUIREMENTS.md`; decision status and rationale remain traceable to the legacy SD records during transition.
