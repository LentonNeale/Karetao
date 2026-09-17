# Energized-Motion Safety Release Checklist

**Authority:** [CTO Final Decisions](Conversations/CTO_DECISION_FINAL.md), SD-25 and exceptions 1-7

Do not authorize energized motion until every row has a recorded artifact at its stated location and independent review accepts it. Firmware tests and builds are not substitutes for hardware evidence or external safety assessment.

| Release blocker | Evidence class | Owner | Required evidence location | Status |
| --- | --- | --- | --- | --- |
| Machine risk assessment and required PL/SIL target | External safety assessment | Functional safety engineer | `Documentation/Evidence/safety/risk-assessment/` | BLOCKED: no artifact recorded |
| Independent E-stop path | Hardware evidence | Electrical/safety lead | `Documentation/Evidence/safety/e-stop/` | BLOCKED: no artifact recorded |
| Hardware motor-disable or power-removal path | Hardware evidence | Electrical/safety lead | `Documentation/Evidence/safety/motor-disable/` | BLOCKED: no artifact recorded |
| Watchdog behavior and fault recovery | Firmware and hardware evidence | Firmware lead, electrical lead | `Documentation/Evidence/safety/watchdog/` | BLOCKED: no artifact recorded |
| Actuator stop/brake/power behavior | Hardware evidence | Mechanical and motor-integration leads | `Documentation/Evidence/safety/actuator-stop/` | BLOCKED: no artifact recorded |
| Fault indication and operator-visible reporting | Firmware and hardware evidence | Firmware lead, system integrator | `Documentation/Evidence/safety/fault-indication/` | BLOCKED: no artifact recorded |
| Reset behavior and explicit non-automatic reactivation | Firmware evidence | Firmware lead | `Documentation/Evidence/safety/reset-recovery/` | BLOCKED: no artifact recorded |
| Measured stopping time in hazardous operating conditions | Hardware evidence | Safety engineer, mechanical lead | `Documentation/Evidence/safety/stopping-time/` | BLOCKED: no artifact recorded |
| Exact MKS controller model, firmware, command, feedback, and brake behavior | Hardware evidence | Motor-integration lead | `Documentation/Evidence/motor-controller/` | BLOCKED: no artifact recorded |
| CAN physical layer, bitrate, load, termination, topology, and recovery | Hardware evidence | CAN/integration lead | `Documentation/Evidence/can/` | BLOCKED: no artifact recorded |
| SPI clock, Pi driver, DMA, GPIO, polling, host-stall, and signal-integrity acceptance | Hardware evidence | Pi/firmware integration lead | `Documentation/Evidence/spi/` | BLOCKED: no artifact recorded |
| Versioned payload schema and conversion evidence before replacing processed millidegrees with radians | Firmware evidence | Firmware lead, Pi integration lead | `Documentation/Evidence/payload-schema/` | BLOCKED: no artifact recorded |
| Calibration flash schema, CRC, power-loss, sector allocation, and endurance test evidence | Firmware and hardware evidence | Firmware lead, validation lead | `Documentation/Evidence/calibration-flash/` | BLOCKED: no artifact recorded |
| Applicable safety-rated relay/controller and safety architecture | External safety assessment | Functional safety engineer, electrical lead | `Documentation/Evidence/safety/architecture/` | BLOCKED: no artifact recorded |

## Review Record

Release review owner: Functional safety engineer. The review record, exceptions, and final release decision belong in `Documentation/Evidence/safety/release-review/`. Missing, failed, or unreviewed evidence keeps the release blocked.

## Source Traceability

SD-25 is covered by the risk assessment/PL-SIL, independent E-stop, motor-disable/power-removal, watchdog, actuator stop/brake, fault indication, reset behavior, and safety-rated architecture rows.

CTO exception 1 maps to risk assessment/PL-SIL; 2 to E-stop, motor-disable, watchdog, actuator stop/brake, and stopping-time evidence; 3 to exact controller and CAN evidence; 4 to SPI evidence; 5 to the versioned radians payload-schema row; 6 to calibration-flash test evidence; and 7 to the blocked-status rule and release-review record.

## Scope Boundary

The STM32/Pi heartbeat, lifecycle, CAN, time-sync, and command-gating behavior are supplementary application controls. They are not an independent safety function and do not establish a PL/SIL rating.