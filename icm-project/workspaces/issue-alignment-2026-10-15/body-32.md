## Context

Charter goal 3 (links measured, Stage 3), register item LIVE-22. Characterise the sensor acquisition timing and end-to-end measurement age on target hardware. `PRM-ACQ-02` records an approximately 46 ms six-axis sweep, measured on a Debug build; it does not give the timing of each axis on its own.

The estimator items of the original text (EKF consumption latency, estimator timing contract) are withdrawn: a high-rate state estimator is a charter non-goal (`PROJECT_CHARTER.md`) and LIVE-07 is closed as not planned. This is bench work and cannot start until the bench is wired and powered (`Hardware/bench-wiring/BRING_UP.md`).

## Scope

Measure and document, up to the Raspberry Pi receipt:

- per-axis acquisition period and acquisition timestamp;
- inter-sensor observation skew (target `PRM-TS-02`) and acquisition jitter;
- sensor-to-STM32 processing latency and STM32-to-SPI transport latency;
- Raspberry Pi receive and processing latency;
- end-to-end measurement age, representative and worst case;
- reconciliation of the per-axis numbers with the measured six-axis sweep.

Distinguish physical acquisition time from snapshot availability time.

Register rows this issue moves from Provisional to Measured (ruled 2026-10-15): `PRM-ACQ-01`, `PRM-ACQ-02` (re-measured with four fitted axes), `PRM-ACQ-05` and `PRM-TS-02`. It also hosts Gate B for `PRM-TS-01` (±1 ms against an independent reference), which #42 points here.

## Acceptance Criteria

- [ ] Per-axis acquisition timing, periods, jitter and skew are measured on target hardware, with an evidence record each (`EVIDENCE_RECORD_FORMAT.md`).
- [ ] Acquisition timestamp semantics are documented once, in the timing documents.
- [ ] End-to-end measurement age is measured or bounded, with representative and worst-case behaviour.
- [ ] The sweep time is reconciled with the per-axis measurements.
- [ ] The register rows closed by this issue show the new basis, with the record linked.

## Verification / Evidence

Evidence records carrying the `VERSION` identity from a clean build; the register rows are updated in `PARAMETER_REGISTER.md`.

## References

- `Documentation/01_SYSTEM/SYSTEM_SYNCHRONIZATION.md`; `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`
- `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md` (`PRM-ACQ-*`, `PRM-TS-*`, "Measurement stages")
- `Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md`; `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` SYS-TS-001
- SD-01, SD-08; register item LIVE-22
