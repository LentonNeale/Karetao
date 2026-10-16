# Issue #80: Implement the latest-value store that owns sample and feedback ageing and the coherent snapshot copy

Date: 2026-10-16. Branch: `issue/80-latest-value-store`. Requirement or ruling served: `SPI_SYSTEM_INTERFACE.md` §8 (snapshot coherency), rulings R15 (stores protected), R10 (31H bytes in the motor record), R16 (sync-quality bits retired), R6 (processed angle from RAW ANGLE); PRM-ACQ-05, PRM-MOT-01.

## Predictions

| Layer | Question | Lenton's prediction | What the source showed | Pointer |
|---|---|---|---|---|
| Requirement | Does today's firmware break §8 coherency, and how? | Not sure | No torn reads today: one cooperative task writes and reads the stores, so a write cannot interleave with serialisation. That changes when R15/B81 moves the sweep to its own task. The records are still incoherent: nothing ever ages a record (freshness is set FRESH at write time and never becomes stale), and the motor record's one `payload` holds whichever of the alternating 31H and 32H replies came last, against R10. | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` §8; `Arm_Sensor_Hub/Documentation/FIRMWARE_ARCHITECTURE.md:195`; `can_service.c:236-243` (poll phases), `:190` (one SetValid for every reply) |
| Contract | How does a v1 snapshot tell the Pi a sensor record is stale? | A spare bit (bit 7) | Not within #80: the schema says freshness "is not on the wire today; whether to serialise it is a separate, versioned schema decision". The precedent for a reserved bit is NOT_FITTED (bit 6, D-10), which needed a decision. In v1 the only expression is bit 0 cleared; `MotorLatestValue_MarkStale` already did that for motors. R10's motor STALE bit lands with #61. | `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md:84-92`; `ARCHITECTURE_DECISIONS.md` R10 |
| Code | Where does `now` come from in CopySnapshot? | Caller passes `now_us` | Held. The store then has no clock dependency, host tests drive ageing with chosen times, and only one clock (TimeService µs) is compared. Using the last accept's timestamp as `now` would recreate the bug: nothing arriving means nothing ages. Edge: a sample stamped after the caller read `now` is age 0, not a wrapped huge age. | issue #80 acceptance criteria; `time_service.h` (µs) vs `HAL_GetTick` (TIM6 ms, `.ioc` `NVIC.TimeBase`) |
| Hardware | During the critical section, what happens to the SPI3 DMA-complete interrupt? | Not sure | Delayed, then runs. `taskENTER_CRITICAL` raises BASEPRI to `configMAX_SYSCALL_INTERRUPT_PRIORITY` (5 << 4 = 0x50), masking priorities 5 to 15; SPI3 (5), DMA1_Stream0 (5), DMA1_Stream5 (6) and TIM6 (15) are all masked. The NVIC latches the IRQ as pending and takes it at exit; the DMA moves the bytes in hardware meanwhile. Only a second event of the same IRQ while masked would merge. So the section holds only a record copy, never serialisation. | `Middlewares/.../ARM_CM4F/port.c:403`, `portmacro.h:191`; `Core/Inc/FreeRTOSConfig.h:144,151`; `Arm_Sensor_Hub.ioc` NVIC lines |
| Hardware (fact, no question) | Which AS5600 register feeds `processed_angle_mdeg`? | n/a | RAW ANGLE (0x0C), per R6. ANGLE (0x0E) is the scaled output with a 10-LSB hysteresis at the 360° limit; with ZPOS/MPOS unwritten they differ only near the wrap. #83 then stops reading ANGLE. | `icm-project/references/as5600/register-map.md` rows 8-9, 25-26 (datasheet pp. 20-21) |

## Plan decisions (Lenton Neale, 2026-10-16)

| Question | Decision | Why |
|---|---|---|
| How does a stale record appear on the v1 wire? | Bit 0 (SAMPLE_VALID / FEEDBACK_VALID) cleared; the last values and their acquisition timestamp are kept | Freshness on the wire is a separate versioned schema decision (`SPI_PAYLOAD_SCHEMA.md:92`); keeping the timestamp lets the Pi see the age; matches the former `MotorLatestValue_MarkStale` |
| Where does #80 stop on the SPI side? | The copy path only: every snapshot build goes store → static copy → `SpiProtocol_SerializeSnapshot`; the GET_SNAPSHOT and periodic triggers stay with #81 and #82 | Those issues own the triggers and are blocked by #80; wiring a periodic stage now would let a SNAPSHOT replace a pending ACK while #82 redesigns that path |
| What motor window does Configure get? | Derived in `app_init.c`: 5 × (2 × PRM-CAN-05 × registered motors), the as-built 31H interval; PRM-MOT-01's note records it until #61 adds the feedback-period row (R11) | No register row gives the commissioned feedback period a number; a new row now would be replaced by #61 |
| How are the serialised bytes tied to the Python side? | `get_snapshot_staged` is regenerated to what the store produces, and a C test feeds the store, copies, serialises and compares with it | One file, already decoded field by field by the Python suite; the README's lockstep rule (C, Python, file in one commit) |

## Code review (`/code-review high`, 2026-10-16)

| # | Finding | Verdict | Outcome |
|---|---|---|---|
| 1 | The scheduler polls 30H (`CommandCode::EncoderValue`, `command.hpp:14`) but the store accepted only 31H, so no position would reach the snapshot on the bench | Confirmed (`ARCHITECTURE_DECISIONS.md:45`: "the CAN service still polls 30H and 32H") | Fixed, Lenton's choice: 30H accepted as POSITION (carry × 0x4000 + value); the v1 record carries the raw 30H reply; 31H moves with R11 in #61 |
| 2 | The decoder's `has_status` guess (first byte 0 or 1) set CONTROLLER_STATUS_VALID for an encoder reply, which has no status byte | Confirmed | Fixed: position feedback carries no status; `status` 0 and bit 1 never set; service test covers a 0x00-led reply |
| 3 | One bad motor row made `LatestValue_Configure` reject everything, shown as six NOT_FITTED axes | Confirmed | Fixed: `app_init` refuses the row alone (joint > 5) and counts it as an MKS register failure |
| 4 | ML/MH still invalidate, against R6 | True, owned by #91 (B74) | Not changed here (plan decision) |
| 5 | ANGLE still read though unused | True, owned by #83 | Not changed here; no new failure mode |
| 6 | "Fitted" held in the sensor task and the store | True; diverges only on a rejected `ConfigureFittedAxes`, already counted | Open question below |
| 7 | Motor window from table rows | Partly | Fixed: from the registered motors; poll period has no runtime caller |

Second pass (`/code-review high`, after the fixes above). Lenton's ruling: stay in scope.

| # | Finding | Outcome |
|---|---|---|
| 1 | The motor window assumes one poll per 20 ms, but the single loop runs at sweep speed, so 200 ms covers about two or three polls | Recorded in PRM-MOT-01's note; the number waits for #61's commissioned feedback period |
| 2 | The sensor window of 100 ms is about two sweeps at the measured 46 ms | Recorded in PRM-ACQ-07's note; the value is the one the issue fixed; Stage 3 measures it |
| 3 | ANGLE still read | Out of scope (#83) |
| 4 | Duplicate `motor_index` rows counted twice and silently overwritten | Fixed: the duplicate row is refused and counted |
| 5 | Failed reads timestamped, then discarded by the store | Fixed: the unused clock read is dropped (and the include) |
| 6 | Fitted and registered held twice; refusals dropped | Out of scope (Lenton cancelled) |
| 7 | `raw × 360000` overflows uint32 above 11930 | Fixed: a raw count above 4095 is refused; tested |
| 8 | Half of R6 applied | Out of scope (#91) |
| 9 | `app_init` repeated the store's joint limit | Fixed: `LATEST_VALUE_MAX_LOGICAL_JOINT` exported |
| 10 | A Configure failure was counted as a sensor failure | Fixed: own counter `g_app_store_configure_failures_dbg` |

Why the host tests missed 1 and 2: `service_test_main.c` stubs `mks_decode` and injects a decoded reply, so neither the request code nor the decoder's real behaviour runs in a test. A test that encodes the request and decodes a real reply needs the MksServo library linked into a host test (a #61 concern).

## Concepts met

- **Torn read**: a reader sees some fields of a record from one write and some from the next; needs a writer that can preempt the reader (or the reverse), which R15's separate sensor task introduces.
- **Copy-out under lock**: hold the lock only for a `memcpy` of the records into the caller's buffer, then do the expensive work (serialisation) on the private copy; keeps the masked-interrupt window to microseconds.
- **BASEPRI masking**: the Cortex-M4 register FreeRTOS uses for task critical sections; it masks by priority instead of disabling all interrupts, so priorities 0 to 4 still run (and must never call the kernel).
- **NVIC pending latch**: a masked interrupt is remembered as one pending bit and taken when the mask drops; two events of one IRQ while masked merge.
- **Freshness at read time**: staleness is a function of `now − acquisition time`, so it must be judged when the record is read; a producer that has stopped cannot mark its own record stale.
- **Time as a parameter (functional core)**: the store takes `now_us` from its caller, so it depends on no clock and host tests control time exactly.
- **Big-endian encoder replies**: the MKS 30H reply carries an int32 carry and a uint16 value (0..0x3FFF, one carry per turn), the 31H reply an int48 cumulative value, all big-endian (`mks-servo42d-57d-can/frame-and-checksum.md` row 17, `read-commands.md` rows 7-14).
- **Implicit function declaration**: C89 lets a call to an undeclared function compile with an `int` return; losing `time_service.h` through the removed header would have truncated the 64-bit timestamp. The warning caught it; `can_service.c` now includes the header itself.
- **Test doubles hide integration faults**: a stub that returns the decoded value the test wants proves the code above it, never the boundary it replaces (findings 1 and 2).

## What the change did and how it was verified

One module, `latest_value.c`, now owns the newest sample per axis and feedback per motor. Producers only accept (the sensor task as a classified sample, the CAN service as typed 30H position or 32H speed); the SPI service copies the store under a FreeRTOS critical section into its own static buffer and `spi_protocol.c` serialises that copy, so no record changes during serialisation or DMA (§8). Freshness is judged at copy time from the caller's `now` (PRM-ACQ-07, PRM-MOT-01); a stale record goes out with bit 0 clear and its data kept; bit 5 (and the motor's bit 2) is retired per R16 on both sides. The shared golden snapshot is regenerated to what the store produces, and both suites assert it.

Checks run (2026-10-16, after both review passes): HostTests 6/6 (store ageing, refused writes, critical-section counts, CAN typed feedback, the store reproducing the golden payload byte for byte, shown to fail on a flipped byte); the Debug and Release builds with the stack check (defaultTask deepest path 452 B Debug and 368 B Release, against 524 B and 416 B on main; IDLE and Tmr Svc unchanged); the Pi suite (229 tests); `make_vectors.py --check`; `doc_check` clean. Not run: `tools/check-sensors.sh` (needs the board; syntax-checked only) and any bench test. Two `/code-review high` passes; their in-scope findings are fixed (tables above).

## Open questions

- `mks::decode::decode` still guesses `has_status` from the first payload byte for every reply; the store no longer uses it for encoder replies (review finding 2), but any later consumer of `CanService_GetLastResponse` should know.
- "Fitted" lives in the sensor task (`s_axis_fitted`) and in the store (review finding 6); one owner would need the store to answer a query, beyond the four-call interface #80 set.
- #81 and #82: the comments naming the copy-and-serialise path are posted with the merge.
- `PARAMETER_REGISTER.md` PRM-ACQ-05's note still says PRM-ACQ-01 is 100 Hz; PRM-ACQ-01 has been 20 Hz since 2026-10-03.
