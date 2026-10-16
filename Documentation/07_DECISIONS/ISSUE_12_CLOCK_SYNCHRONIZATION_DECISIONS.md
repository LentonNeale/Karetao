# Issue #12 — Clock Synchronization: Final Decisions (Full Collation)

**Status:** Living decision record for a single-maintainer project. Recorded
as the current contract in effect, not frozen. Items explicitly marked
*recommended, not yet reconfirmed* are my recommendation only — everything
else has been discussed and settled in this conversation. This document
collates recommendations already made; it does not introduce new ones.

**Charter note (2026-10-03):** the high-rate estimator named below as the consumer of synchronized timestamps is a charter non-goal; ClockSync remains the model, and its consumers are the snapshot decoder and evidence tools (PROJECT_CHARTER.md).

Structured against the original ten Issue #12 items, plus one item
(liveness/motion-safety timeout) that emerged from discussion beyond the
original ten.

---

## 1. TIME_SYNC response wire format

**Final:** every outgoing SPI message carries the existing `seq` field as
its unique exchange ID (see item 5 — no separate `sync_seq` is introduced).
A new field, `request_received_local_us`, is added via a versioned payload
extension on every applicable response that contributes a ClockSync
observation (not diagnostic-only). `frame_time_us` is untouched. This is
the dense, per-message approach (refactored-Klipper direction), superseding
the earlier single-dedicated-message design.

---

## 2. T1 / T2 / T4 definition

**Final:**
- `T1` = Pi request send time (`monotonic_us()`), `T4` = Pi response
  receipt time. `T_pi_obs = (T1 + T4) / 2` is the Pi-side observation
  instant.
- `T2` (the STM32 event) = the **raw TIM2 counter captured in the
  DMA-complete ISR** (`dma_complete_raw`), *not* `TimeService_NowUs()` and
  *not* `response_staged_us`. `TimeService_NowUs()` is not ISR-safe — it
  mutates `last_counter`/`wrap_base_us` — and `response_staged_us` occurs
  later than actual reception.
- The raw ISR value is extended to a 64-bit local timestamp in a separate,
  serialized **task-context** step. That task-context-extended value is
  what is ultimately carried on the wire as `request_received_local_us`.

---

## 3. 32-bit raw vs. 64-bit `TimeService_NowUs()` for ClockSync

**Final:** ClockSync consumes the 64-bit extended value produced by item
2's task-context extension step — not a raw 32-bit counter directly. This
confirms the earlier decision to use `TimeService_NowUs()`, refined to
clarify that the extension itself happens outside the ISR, not inside it.

---

## 4. Reuse of pipelined-response correlation machinery

**Final:** extend `TimingSession.transact()` (`timing.py`) to call
`ClockSync.record_exchange()` on every correlated exchange. No second
outstanding-request table is added in `spi_device.py`. `_MAX_PENDING =
4096` is left unchanged unless the design later moves to
asynchronous/multi-outstanding transactions.

**Amended 2026-10-16 (Lenton Neale, #78; designed in the 2026-10-15
architecture review):** the intent stands: one outstanding-request table,
reused for clock sync. The table is now `ExchangeSession`'s (`exchange.py`,
grown from `TimingSession`; one session owns the link, and other consumers
read its records), and the call direction is reversed: the session
does not depend on ClockSync. Each correlated `TransactionRecord` carries T1
(`t1_request_sent_ns`), T2 (`request_received_local_us`, once item 1 fixes its
wire placement) and T4 (`t4_response_received_ns`), so one record is one
observation, and ClockSync's owner feeds `ClockSync.record_exchange()` from
the records.

---

## 5. `seq` versus `sync_seq`

**Final:** no separate `sync_seq` concept is introduced. The existing
Pi-side request `seq` is the exchange-correlation ID for ClockSync
purposes. Note: STM32 and Pi have independent sequence spaces, so `seq` is
not a single globally-unique ID across both directions — but since the Pi
always initiates, its own `seq` is sufficient for this purpose.

---

## 6. Validity hierarchy

**Final:** two separate chains, not one combined hierarchy:
- **STM32-side:** liveness (`link_stale`, count-based — see item 11)
  directly and locally gates STM32 motion permission, fail-closed.
- **Pi-side:** `ClockSync.is_valid()` governs timestamp-conversion
  validity / measurement usability, feeding EKF acceptance.

These are independent signals: `link_stale` is not derived from
ClockSync's sync quality, and `ClockSync.is_valid()` does not itself drive
motion permission within Issue #12's scope.

---

## 7. Sensor timestamp migration

**Final:** the STM32 performs no clock math (per the decision that it only
tracks its own internal time). The acquisition-instant timestamp is
captured on STM32 as raw local time; the Pi's ClockSync model converts it
to produce the synchronized `measurement_timestamp_us` consumed by the
estimator. `frame_time_us` (frame assembly time) and
`request_received_local_us` (exchange-timing observation, item 1) remain
distinct, untouched fields from this one.

---

## 8. Diagnostics schema changes

**Final:** introduce DIAGNOSTIC v2 via explicit schema-version dispatch (a
v1 decoder stays v1-only; v2 is explicitly selected), implemented alongside
a working `GET_DIAGNOSTIC` request path (currently missing —
`GET_STATUS` returns ACK today). In scope for Issue #12.

*Recommended, not yet field-by-field reconfirmed:* v2 content = existing
v1 fields unchanged, plus the ClockSync field set — `sync_valid`,
`sync_sample_count`, `rejected_sample_count`, `estimated_frequency_hz`,
`estimated_frequency_error_ppm`, `reference_pi_time_us`,
`reference_stm32_time_us`, `current_offset_us`, `min_half_rtt_us`,
`last_sync_age_us`, `prediction_stddev_us` — with the existing top-level
`time_sync_valid` becoming a derived/summary field rather than an
independently-maintained one.

---

## 9. Retirement of TimeSyncSession estimator responsibilities

**Final migration mapping:**
- candidate/offset storage → history-recorder role
- offset acceptance + frequency estimation → ClockSync
- RTT statistics → `time_sync_analysis.py`
- timestamp conversion → ClockSync
- existing drift-limit rejection → kept **temporarily** as a transitional,
  secondary diagnostic check (must not independently modify ClockSync
  state or create a second acceptance policy); removed in a later cleanup
  issue once ClockSync is hardware-validated.

---

## 10. Separating clock-model characterization from ±1ms validation

**Final:** treat as two separate, sequential acceptance gates, using the
evidence classification already used elsewhere in the repo (UNIT /
INTEGRATION / HW):
- **Gate A — model characterized:** synthetic + integration tests (Phase
  A/B) show the regression model converges and behaves correctly.
- **Gate B — ±1ms timestamp accuracy validated:** a separate,
  hardware-validated milestone (Phase C) against an independent reference,
  attempted only after Gate A passes.

Document explicitly (per the repo's existing evidence) that current
exported measurement timestamps are **not yet** in the required
synchronized domain — Gate A passing does not imply Gate B is met.

---

## 11. STM32 liveness / motion-safety timeout (emerged beyond the original ten)

**Final:** a single authoritative mechanism, replacing both the old fixed
500ms Pi-heartbeat motion-safety timeout and the earlier fixed-5s
`link_stale` draft:

- **`link_liveness_timeout_us` → count-based:** `missed_count` increments
  once per expected-message interval with no accepted, valid SPI message;
  resets to 0 on any accepted, valid message. Trip threshold is
  `missed_count >= N_moving` while the arm is moving, or `>= N_idle` while
  idle, with `N_moving < N_idle`.
- **`counter_extension_gap_us` stays separate** — a fixed, non-dynamic
  guard purely for the 32-bit TIM2 wrap-extension ambiguity, currently
  500ms, explicitly flagged for review once hardware characterization data
  exists. It must remain fixed/conservative, not dynamic, since making it
  dynamic would add ambiguity to the exact thing it exists to remove.
- **On trip:** `link_stale = true`, motion gate fails closed (item 6);
  clears on the next accepted, valid message.
- This changes an already-documented safety contract
  (`SYS-SYNC-002/004/005` and the existing 500ms heartbeat spec), so it
  needs a requirements/verification-evidence update, not just a code
  change.
- **Still open:** exact `N_moving`/`N_idle` values, the source of
  `expected_message_interval_us`, the motion-state signal input to the
  check, and the recovery behavior after a rejected counter-extension gap.

---

## Implementation sequencing (as previously recommended)

1. Resolve `link_stale`/motion-gate mechanism (item 6), built count-based
   from the start (item 11).
2. Freeze ClockSync ownership and acceptance semantics.
3. Add ISR raw-counter capture + task-context 64-bit extension with the
   `counter_extension_gap_us` guard (item 11) and its still-open recovery
   behavior.
4. Add `request_received_local_us` to the versioned wire schema (item 1).
5. Feed `ClockSync.record_exchange()` from the `ExchangeSession`
   transaction records (item 4, as amended 2026-10-16).
6. Implement DIAGNOSTIC v2 + `GET_DIAGNOSTIC` (item 8).
7. Migrate/remove STM32 `SyncStateAccept`/`Refresh` (architecture change
   underlying items 3/7).
8. Update Pi `TimeSyncSession`, retaining the transitional drift check
   (item 9).
9. Update `protocol_test_main.c` / `service_test_main.c`.
10. Update system requirements, interface documentation, and verification
    evidence — including the item 11 motion-safety requirement change, and
    the item 10 evidence-gate documentation.

---

## Architectural invariant

```
STM32 acquisition timestamp
        |
        v
STM32 local monotonic clock
        |
        v
ClockSync conversion model  <---  SPI receive timestamps (observations)
        |
        v
synchronized measurement_timestamp_us
```

The SPI receipt timestamp feeds the clock model; it never replaces the
measurement acquisition timestamp.
