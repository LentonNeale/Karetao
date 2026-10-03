# CAN integration evidence

**Status:** Evidence collection in progress; no hardware measurement yet

---

## Bitrate: target versus generated configuration

Target PRM-CAN-01, generated PRM-CAN-02, candidate PRM-CAN-03 (values in `PARAMETER_REGISTER.md`). 
Generated configuration (`Arm_Sensor_Hub.ioc` and `MX_CAN1_Init()`):

- 875 kbps: prescaler 16, BS1 1 TQ, BS2 1 TQ, SJW 1 TQ.
- Sample point 66.7%; APB1 clock 42 MHz.

A candidate configuration for the target bitrate exists (from `CAN_BIT_TIMING_EVIDENCE.md`):

| Setting | Candidate value |
| --- | ---: |
| Prescaler | 3 |
| Sync segment | 1 TQ |
| BS1 | 11 TQ |
| BS2 | 2 TQ |
| SJW | 1 TQ |
| Sample point | 85.7% |

This is a **reproducible calculation, not an approved configuration**. Adopting it requires:
- CubeMX integration (update `.ioc` and re-generate);
- STM32 bxCAN controller validation (error handling, bus-off recovery, retransmission policy);
- Physical-layer validation (signal integrity, bit stuffing, worst-case load, error rates, startup/stall/fault behavior).

---

## CAN Bitrate Validation Evidence

**Reference:** the former `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md` (git history)  
**Status:** Engineering calculation; not hardware validation  
**Date recorded:** As of 2026-09-20

### Evidence Provided

1. **Source configuration:**
   - System clock: 168 MHz
   - APB1 prescale: 4 → PCLK1 = 42 MHz
   - Current generated bitrate: 875 kbps
   - Candidate bitrate: 1 Mbps with 85.7% sample point

2. **Provisional bus-load estimate:**
   - Standard 11-bit CAN frame with 8 data bytes ≈ 111 bits (≈ 130 bits worst-case with stuffing)
   - Single motor: 100 frames/s (50 polls/s + 50 responses/s) = 1.3% load
   - Eight motors, 100 Hz command rate: 2,400 frames/s = 31.2% load
   - Both estimates below 50–60% target; neither is a validated worst case

3. **Known unknowns:**
   - Exact MKS controller model, firmware, command/response rate
   - Actual controller traffic, command modes, retries, error frames
   - Physical topology, cable length, termination, shielding
   - Measured sample point, SJW margin, retransmission behavior
   - Logic-analyzer or CAN-analyzer evidence of actual bitrate under load

### Open items before the Stage 3 measurement

1. Exact MKS controller model, firmware, command/response lengths, feedback rate, required polling/command traffic.
2. CAN transceiver part, supply/standby behavior, common-mode range, signal levels.
3. Bus topology, cable type/length, node count, stub lengths, shielding, grounding, 120-ohm termination.
4. Oscillator tolerance, measured sample point/SJW margin, retransmission policy, bxCAN bus-off recovery behavior.
5. Logic-analyzer or CAN-analyzer evidence of actual bitrate, error counters, arbitration latency, worst-case load, stability through startup/stalls/faults.

**None of these items is currently satisfied.**

---

## Verification

Rows SYS-MOT-001, SYS-MOT-002 and the CAN interface row in `SYSTEM_VERIFICATION_MATRIX.md` carry the verification status; measurements are recorded per `EVIDENCE_RECORD_FORMAT.md` (Stage 3, `PARAMETER_REGISTER.md`, Measurement stages).

---

## Provenance

Reconciled from `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md`. This is **evidence material, not a system requirement**. The evidence documents an engineering calculation and provisional bus-load estimate, not hardware validation. The candidate 1 Mbps configuration is recorded but not approved. The bitrate difference between target and generated configuration is recorded for the Stage 3 measurement.
