## Context

The clock-synchronization decisions recorded in `Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md` (2026-09-24), as amended by ruling R16 and by rulings R14(d) and R22 for the parts that moved (table "Code-review rulings (2026-10-14)" in `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`), settle the acquisition-timestamp and time-reference design (SYS-SYNC-001, SYS-TS-001). The firmware and Pi code still implement the superseded one-way `TIME_SYNC` with an STM32-held offset.

This issue tracks implementing that design in one lockstep change across both sides of the SPI link. The Agent Brief in the comment of 2026-10-15 is the working specification. #45 is the removal half and closes with this issue. The former parent LentonNeale/Karetao#46 (LIVE-07) is closed as not planned (EKF non-goal); the consumers of synchronized timestamps are the snapshot decoder and the evidence tools.

## Scope

1. ISR raw TIM2 capture at the end of the SPI transfer that carried the request, extended to 64 bits in task context, guarded by the fixed `counter_extension_gap_us` (PRM-TS-04).
2. `request_received_local_us` appended to ACK, VERSION and the correlated SNAPSHOT (schema version 2), never to NACK, in C, Python and shared golden vectors.
3. Pi `ClockSync` model fed by every correlated exchange; one raw monotonic clock; a backwards step in STM32 time invalidates it; plausibility rejection is the single acceptance policy; record timestamps are converted and marked SYNCHRONIZED only from `ClockSync.is_valid()`.
4. Removal of the STM32 `TIME_SYNC` message handling, the held offset, the sync-quality validity bits and the legacy Pi `TimeSyncSession` chain including its drift check; the two as-built TIME_SYNC documents are deleted with a provenance pointer.
5. Tests on both sides, including Gate A (synthetic and integration tests show the model converges).

Moved elsewhere by the rulings, not part of this issue:

- Count-based `link_stale`, `N_moving`/`N_idle` and the gate inputs: #64 (ruling R22).
- DIAGNOSTIC v1 on message 0x03 and `GET_DIAGNOSTIC` 0x15: #61 (ruling R14). ClockSync fields stay a Pi-side record and are not wire content (R14(d)), so there is no DIAGNOSTIC v2.
- Gate B (±1 ms on hardware against an independent reference, PRM-TS-01): #32.

## Open parameters from the original text

- [x] `N_moving` / `N_idle` values, expected-message-interval source, motion-state input: answered by R22 (Provisional values, a fixed STM32 constant, non-zero MKS speed counts as moving), implemented under #64.
- [x] DIAGNOSTIC layout and the `GET_DIAGNOSTIC` message value: answered by R14.
- [x] Recovery after a rejected counter-extension gap: the reply goes without the field and a counter increments (stated in the Agent Brief).
- [x] ClockSync plausibility thresholds: `PRM-TS-06` (Provisional, 2026-10-15): reject an exchange whose half round-trip exceeds 2 × the running minimum or whose offset residual exceeds `PRM-TS-01`; a rejected exchange is counted and does not update the model. Confirmed or revised from the Gate A data.

## Acceptance Criteria

- [ ] Every acceptance criterion of the Agent Brief is met.
- [ ] Gate A passes on both sides; Gate B is tracked in #32 and not claimed here.
- [ ] The remaining open parameter above is decided and recorded in the authoritative documentation.
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean; the task stack check passes.

## References

- `Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`; `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` rulings R14, R16, R22
- `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`; `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md`
- `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`: SYS-SYNC-001 (absorbs the retired SYS-SYNC-002 to 006) and SYS-TS-001; SYS-LINK-001 (the former SYS-FAIL-001)
- Removal half: #45. Gate B: #32. Link liveness: #64. DIAGNOSTIC: #61.
