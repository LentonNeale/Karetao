⚠ **ARCHIVED — Non-normative historical document**

- **Archived:** 2026-09-20
- **Historical status:** Sprint planning and completion reports, obsolete
- **Superseded by:** Current project state in `Documentation/` and `07_DECISIONS/`

---

# Sprint 2 Readiness Report - Arm Sensor Hub

Date: 2026-09-07  
Repository: `LentonNeale/Arm_Sensor_Hub`  
Prepared from current implementation and contract baseline in `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation`.

## 1) Executive Summary

Sprint 1 established a strong contract-first architecture and host-test baseline for protocol/data-plane primitives. The project is now ready to enter Sprint 2 focused on **integration hardening**: wiring currently host-validated logic into full STM32 runtime behavior, completing SPI/CAN hardware-facing paths, and closing safety/activation gaps before energized-motion release work.

The project is in a **good engineering position**, but it is not yet at a hardware-validated integration milestone.

## 2) Current State by Area

### A. Architecture and lifecycle
- Service-oriented architecture is in place across lifecycle, sensor, CAN, SPI, time, and snapshot domains.
- Lifecycle state model exists and is used across major services.
- Recovery and activation boundaries are documented with explicit constraints against automatic unsafe motion resumption.

### B. Build and test baseline
- CMake presets exist for `Debug`, `Release`, and `HostTests`.
- Focused host validation target exists (`sprint1_protocol_tests`) and is documented as the narrow Sprint 1 validation path.
- In current environment, target (`arm-none-eabi`) toolchain availability remains an external runner dependency.

### C. Sensor pipeline
- AS5600 integration path is implemented with diagnostics and latest-value representation.
- Current active sampling behavior is still effectively single-channel execution; six-channel scheduling remains open integration work.

### D. Time and synchronization
- 64-bit monotonic microsecond service exists.
- Time-sync runtime state and validity/timeout model exist.
- Integration of TIME_SYNC acceptance via full SPI command path is not complete end-to-end.

### E. Snapshot/coherency/serialization
- Snapshot frame ownership model (double-buffer semantics) is implemented and host-tested.
- Payload constants/limits and CRC framing utility are in place.
- Final serializer integration against frozen payload contract and live producer data remains partially open.

### F. SPI service
- SPI protocol state machine and response framing logic are implemented and host-tested.
- DATA_READY ownership rules and poll recovery behavior are present.
- Hardware DMA/NSS callback integration and measured hardware acceptance evidence remain open gates.

### G. CAN service
- CAN service includes queue, bounded retry, and bus-off policy primitives.
- RX decode and latest-value updates are implemented.
- Full hardware evidence and some final integration semantics remain gated by real bus/controller measurements.

### H. Health and fault observability
- Health monitor remains mostly scaffold-level and requires fuller system-level aggregation behavior.
- Fault/event lifecycle coupling needs expansion for Sprint 2 operations and diagnostics readiness.

### I. Safety and release posture
- Safety release checklist exists and correctly separates firmware behavior from independent safety evidence.
- Formal safety validation and energized-motion release evidence remain explicitly blocked, as intended.

## 3) Key Risks Entering Sprint 2

1. **Integration risk:** host-tested modules may diverge from on-target behavior when wired to DMA/NSS/CAN hardware paths.  
2. **Activation/safety risk:** incomplete command-gating and recovery coupling can reintroduce unsafe edge cases under communication faults.  
3. **Verification risk:** incomplete CI/toolchain availability may delay early regression detection.  
4. **Configuration risk:** calibration/mapping persistence and recovery behavior are not yet fully closed.

## 4) Recommended Sprint 2 Objectives

## Objective 1 - Complete SPI runtime integration
- Wire DMA start/complete and NSS-abort paths to service state transitions.
- Complete end-to-end request/response + snapshot staging behavior under realistic timing.
- Produce hardware evidence for clock margin, DATA_READY detectability, CRC/sequence behavior under stress.

## Objective 2 - Complete CAN runtime hardening
- Finalize integration of queue/retry/bus-off policy in live command path.
- Validate bus-off detection/recovery behavior on target hardware and capture reproducible evidence.
- Confirm command inhibition/re-activation behavior under fault and recovery sequences.

## Objective 3 - Complete six-channel sensor data plane
- Implement full TCA9548A channel scheduling and latest-value updates across all required channels.
- Ensure mapping/calibration version binding is preserved in records and snapshots.

## Objective 4 - Expand health/fault observability
- Convert HealthMonitor from scaffold to actionable diagnostic aggregator.
- Standardize fault/event emission across lifecycle, transport, sync, and sensor services.

## Objective 5 - Close persistence and startup robustness
- Implement calibration/mapping persistence and safe reload behavior.
- Verify power-loss handling assumptions for persisted data validity.

## Objective 6 - Strengthen verification pipeline
- Keep focused host tests as fast regression gate.
- Add/restore target build evidence once toolchain is available in runner.
- Keep contract-status matrix updated in lockstep with implementation changes.

## 5) Proposed Sprint 2 Workstream Structure

- **Workstream A (Transport Integration):** SPI DMA/NSS + CAN runtime policy wiring.
- **Workstream B (Data Plane):** six-sensor acquisition and snapshot serialization completion.
- **Workstream C (System Robustness):** health/fault aggregation, persistence, startup/recovery edge cases.
- **Workstream D (Verification & Evidence):** host tests, target build evidence, hardware acceptance logs, contract sync.

## 6) Definition of Done for Sprint 2 (Recommended)

- End-to-end sensor->snapshot->SPI flow works on target with reproducible evidence.
- CAN bounded retry/bus-off behavior is validated on real hardware with no silent unsafe resume.
- Six-sensor latest-value pipeline is complete and serialized per contract.
- Health monitor emits actionable diagnostics across service boundaries.
- Persistence/recovery behavior for configuration/calibration is validated.
- Contract docs and status matrix are updated with no contradictions.

## 7) Immediate Next Actions (First Sprint 2 Week)

1. Lock Sprint 2 scope to SPI runtime integration + CAN runtime hardening as first milestone.
2. Assign owners for Workstreams A-D with single integration lead for cross-service sequencing.
3. Add a standing “contract + implementation delta” review checkpoint every merge.
4. Define hardware evidence capture format before test execution to avoid retrospective gaps.

---

This report is intended as the Sprint 2 planning baseline and should be read alongside:
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/CONTRACT_V1_FREEZE.md`
- `/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/SAFETY_RELEASE_CHECKLIST.md`
