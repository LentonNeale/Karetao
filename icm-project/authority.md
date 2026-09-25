# Authority map

The normative model is `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md`. Authority follows subject ownership, not file location. Agents point to the owner and never restate it.

| Subject | Owning document | Notes |
|---|---|---|
| System requirements (SYS-*) | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` | "Proposed" rows are not normative |
| Architecture, lifecycle, timing, sync | `Documentation/01_SYSTEM/` (the matching file) | |
| Interfaces: CAN, SPI, HOST, TIME | `Documentation/02_INTERFACES/<IF>/` | |
| Component roles | `Documentation/03_COMPONENTS/` | Implementation details belong in the component's own `Documentation/` |
| Safety | `Documentation/04_SAFETY/` | |
| Decisions (SD-xx), open questions, LIVE-xx register | `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` | Decision status and rationale |
| Architecture decisions and Issue #12 clock sync | `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`, `ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md` | |
| Arm Sensor Hub implementation | `Arm_Sensor_Hub/Documentation/` | Includes the build contract |
| Raspberry Pi implementation and bring-up | `RaspberryPi_Sensor_Hub/Documentation/` | |
| Vendor behaviour (MKS, AS5600, TCA9548A) | The vendor documents | Reference them; don't rewrite them |
| Issue and tracker rules | `.github/ISSUE_CONTRACT.md`, `.github/ISSUE_FRAMEWORK.md` | |
| Open decisions awaiting the maintainer | `For_Lenton` | Working review list, **not** an authority |

Where documents conflict, the newer decision wins unless it is still marked open or proposed. In that case, flag the conflict to the user.

## Verification authority

`SYSTEM_VERIFIED` is granted only through `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`. Component tests and CI are component evidence only.
