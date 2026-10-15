## Purpose

Produce the calibration and configuration evidence that `SYS-CAL-001` requires. The charter removed the "release conditions" framing; the evidence now feeds the `SYS-CAL-001` row in `SYSTEM_VERIFICATION_MATRIX.md`.

## Scope

Per `SYS-CAL-001` and `SYSTEM_CONFIGURATION.md` §3:

- Versioning and the canonical serialization with its CRC.
- The redundant copy in STM32 flash, and detection of a corrupted copy.
- Power-loss recovery: an interrupted write leaves a valid record.
- The host-side source copy matching the loaded version.
- The controlled transfer path from the Pi or workstation.
- Persisted configuration bound to the validated physical mapping (commissioning).

Flash endurance is outside `SYS-CAL-001` (ruled 2026-10-15): a record is written once per calibration event; see `SYSTEM_CONFIGURATION.md` §3 and `PARAMETER_REGISTER.md` PRM-MCU-02.

Ruling R26 defers calibration to after Stage 4, so this is not on the path to first motion.

## Completion condition

The evidence records for the items above are accepted by Lenton Neale in `SYSTEM_VERIFICATION_MATRIX.md`, each carrying the `VERSION` identity from a clean build (`EVIDENCE_RECORD_FORMAT.md`).

## References

- `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` LIVE-08
- `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md`; `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` SYS-CAL-001
- `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md`; `ARCHITECTURE_DECISIONS.md` ruling R26
- Implementation counterpart: #28
