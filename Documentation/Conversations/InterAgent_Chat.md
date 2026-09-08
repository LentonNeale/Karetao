# InterAgent Chat - Important Notes Outside Sprint Scope

Date: 2026-09-07

## Purpose
Capture important cross-cutting observations that are not direct Sprint task outputs but should be retained for future agent work.

## Notes

1. **Sprint task tracker inconsistency to reconcile** — RESOLVED (2026-09-08)
   - In `Documentation/Sprint_1_List.md`, Task 17 and Task 18 output sections were inconsistent (Task 17 appeared empty while Task 18 referenced policy primitive implementation and remaining integration limits).
   - Fix applied: moved the CAN TX policy/bus-off output to Task 17 (its actual scope) and recorded Task 18 (heartbeat/command-gating) as not implemented, deferred to Motor Service work.

2. **Health monitor maturity gap** — RESOLVED (2026-09-08)
   - `App/Src/health_monitor.c` now implements aggregate level determination (GREEN/YELLOW/RED/UNKNOWN) across I2C, sensor, CAN, and SPI diagnostics via the `copilot/code-audit-phase-2` merge.
   - Remaining open items (thresholds tuning, watchdog ownership) are tracked in `HEALTH_MONITOR_CONTRACT.md`.

3. **Host-validated vs hardware-validated distinction must remain strict**
   - Several capabilities are validated in host tests but still gated for hardware acceptance (SPI DMA/NSS behavior, CAN physical behavior, max SPI clock approval).
   - Recommendation: all Sprint 2 reporting should explicitly label validation class: host, target-runtime, and hardware-integration.

4. **Runner/toolchain dependency risk**
   - Target Debug/Release build evidence can be blocked in environments without `arm-none-eabi`.
   - Recommendation: ensure CI/runner provisioning is addressed early to avoid evidence gaps late in sprint.

5. **Safety-release boundary should not be diluted**
   - Keep current policy that firmware test completion does not imply PL/SIL or energized-motion release readiness.
   - Recommendation: continue linking implementation progress to `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/SAFETY_RELEASE_CHECKLIST.md` blockers.
