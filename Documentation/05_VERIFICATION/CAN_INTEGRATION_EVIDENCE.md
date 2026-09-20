# CAN Integration Evidence and Open Gates

**Status:** Integration gates and evidence collection in progress

---

## C-2 Conflict: CAN Bitrate

### Requirement

SYS-CAN-001 and CAN_SYSTEM_INTERFACE.md both state: **1 Mbps nominal for v1**.

### Current Implementation

- `Arm_Sensor_Hub.ioc` and generated `MX_CAN1_Init()` configure **875 kbps**.
- Configuration: prescaler 16, BS1 1 TQ, BS2 1 TQ, SJW 1 TQ.
- Sample point: 66.7%.
- APB1 clock: 42 MHz.

### Issue

The generated configuration does not meet the 1 Mbps requirement. This is an **implementation gap** (not a documentation error).

### Candidate Resolution

A candidate 1 Mbps configuration exists (from `CAN_BIT_TIMING_EVIDENCE.md`):

| Setting | Candidate value |
| --- | ---: |
| Prescaler | 3 |
| Sync segment | 1 TQ |
| BS1 | 11 TQ |
| BS2 | 2 TQ |
| SJW | 1 TQ |
| Sample point | 85.7% |

This is a **reproducible calculation, not an approved configuration**. Approval requires:
- CubeMX integration (update `.ioc` and re-generate);
- STM32 bxCAN controller validation (error handling, bus-off recovery, retransmission policy);
- Physical-layer validation (signal integrity, bit stuffing, worst-case load, error rates, startup/stall/fault behavior).

### Integration Gate

This conflict blocks CAN integration approval until either:
1. The 875 kbps configuration is accepted as the new system baseline (requires SYS-CAN-001 revision), OR
2. The candidate 1 Mbps configuration is validated and integrated (requires evidence below).

---

## CAN Bitrate Validation Evidence

**Reference:** `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md`  
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

### Integration Blockers (From Evidence)

1. Exact MKS controller model, firmware, command/response lengths, feedback rate, required polling/command traffic.
2. CAN transceiver part, supply/standby behavior, common-mode range, signal levels.
3. Bus topology, cable type/length, node count, stub lengths, shielding, grounding, 120-ohm termination.
4. Oscillator tolerance, measured sample point/SJW margin, retransmission policy, bxCAN bus-off recovery behavior.
5. Logic-analyzer or CAN-analyzer evidence of actual bitrate, error counters, arbitration latency, worst-case load, stability through startup/stalls/faults.

**None of these blockers are currently satisfied.**

---

## CAN Verification Requirements

Before the CAN subsystem can be released to production, verify:

1. **Configuration alignment:** Current or approved bitrate matches SYS-CAN-001 (1 Mbps) or updated requirement.
2. **MKS controller:** Exact model, firmware, command/response timing, and feedback semantics documented.
3. **Physical layer:** Transceiver, cable, termination, topology, and grounding validated against CAN standard and application load.
4. **Bitrate accuracy:** Measured (not calculated) bitrate, sample point, SJW margin, and error behavior on target hardware.
5. **Error recovery:** bxCAN bus-off detection, recovery timing, escalation policy (3 events in 60 s → ERROR state), and reactivation behavior verified under fault injection.
6. **Load testing:** Worst-case traffic (8 motors, 100 Hz commands + polling + error retries) tested with concurrent SPI and sensor acquisition; no frame loss or timeout.
7. **Diagnostics:** All required counters (TX/RX success/failure, queue drops, bus-off events, poll health) confirmed present and correct.

---

## Provenance

Reconciled from `docs/project/firmware/CAN_BIT_TIMING_EVIDENCE.md`. This is **evidence material, not a system requirement**. The evidence documents an engineering calculation and provisional bus-load estimate, not hardware validation. The candidate 1 Mbps configuration is recorded but not approved. The C-2 conflict (1 Mbps required, 875 kbps implemented) is documented for integration decision-making.
