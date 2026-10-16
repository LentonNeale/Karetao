# Issue #78: Implement the Pi ExchangeSession with a firmware-rules fake and a process-wide Sequencer

Date: 2026-10-16. Branch: `issue/78-exchange-session`. Requirement or ruling served: ruling R3 (one process-wide sequencer); `SPI_SYSTEM_INTERFACE.md` §4, §6, §13, §14; `TIME_SYSTEM_INTERFACE.md` §3; Issue #12 item 4 (amended here); design from the 2026-10-15 architecture review (candidate 3, backlog B130).

## Mechanism

Explained layer by layer, no prediction questions (project `CLAUDE.md`, 2026-10-16).

| Layer | What the source shows | Pointer |
|---|---|---|
| Ruling and vocabulary | A *transaction* is one 512-byte clocking; an *exchange* is a request and its correlated reply, two transactions because the protocol is pipelined. R3: one process-wide sequencer on the Pi and one bounded jump after BAD_SEQUENCE. The decision log assigns R3 to B69 = #87, and #87's scope owns the jump, the no-stride rule and the STM32's first-sequence acceptance, leaving the Sequencer's construction here. The document outranks #78's text ("the jump lives there"), so this issue builds the Sequencer without the jump. | `Documentation/01_SYSTEM/SYSTEM_OVERVIEW.md` Vocabulary; `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md:107`; issue #87 |
| Contract | §4: transaction N returns the response staged before N. §6: `seq` monotonic per transmitter, never reused while outstanding. §14: NACK `status_code` 5 BAD_SEQUENCE, 8 BAD_STATE. TIME §3: T1 Pi send time, T2 `request_received_local_us`, T4 Pi receive time. The wire placement of `request_received_local_us` is still open, so the record carries the field as None until #42. | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` §4, §6, §13, §14; `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md` §3; `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md:267` |
| Code (firmware rules the fake copies) | `SpiProtocol_ValidateRequest` checks magic, version, length, CRC, sequence, type, TIME_SYNC payload in that order; an accepted request moves the high-water mark; GET_SNAPSHOT with a snapshot staged gets SNAPSHOT (response_to_seq patched), GET_VERSION gets VERSION, the rest ACK. `SpiSlaveService_RequestAllowed` NACKs BAD_STATE after validation without moving the mark (TIME_SYNC allowed while INACTIVE). The boot DIAGNOSTIC is the first staged frame. Every processed request stages exactly one response. | `Arm_Sensor_Hub/App/Src/spi_protocol.c:208-251`; `Arm_Sensor_Hub/App/Src/spi_slave_service.c:145-150,190,276-320` |
| Hardware | SPI is full duplex: while the Pi shifts request N in on MOSI, the STM32 shifts out on MISO what it handed to DMA before NSS fell, and it sees request N only when `HAL_SPI_TxRxCpltCallback` fires at the end. That is the one-transaction delay. `xfer2` holds CS for the whole 512 bytes. A slave with nothing armed still gets clocked, and the Pi reads idle MISO (the fake's garbage mode). | `icm-project/references/stm32f4-hal-cmsis/spi-dma-gpio-tick.md:7-16`; `icm-project/references/linux-spidev/py-spidev-api.md:26` |

## Decisions

| Question | Decision | Why |
|---|---|---|
| Where does R3's bounded jump go? | #87, with its register row and the firmware's first-sequence acceptance; this issue builds the Sequencer only. | The decision log assigns R3 to B69 (#87), and the jump only works once the STM32 side exists. Plan confirmed by Lenton. |
| `exchange()` budget default | Required, no default. | No register row holds a value (Numbers rule); #102's callers set it. |
| `TimingSession` | A thin subclass of `ExchangeSession` with the old signature, until #102. | One implementation; the harness keeps working unchanged. |
| Issue #12 item 4 says `TimingSession.transact()` calls `ClockSync.record_exchange()`; the 2026-10-15 design says the session has no ClockSync dependency | Amend the documents to the 2026-10-15 design (Lenton Neale, 2026-10-16). | Keeps the dependency one way (transport does not know the time model); one correlated record is one observation; item 4's intent (one correlation table) is unchanged. |

## Concepts met

- **Pipelined request/response**: the reply to a request rides in a later transaction, so correlation is by sequence through a pending table, never by position.
- **Full-duplex SPI slave with DMA**: the slave can only transmit what it armed before the clock starts, which is the physical reason for the pipeline.
- **Result object versus exception**: firmware outcomes (NACK, lost reply, garbage) are expected events on a link and come back as `ExchangeResult` outcomes; only caller errors (a budget below two) raise.
- **Dependency direction**: the session produces records and ClockSync's owner consumes them, so the transport layer can be tested without the time model.
- **Contract fake**: one fake that enforces the firmware's rules and is pinned to the shared golden frames. This issue adds it; the five older fakes, which each model the firmware differently, stay until #102 moves their users onto it and deletes them.
- **Mutation check**: break the code on purpose and confirm a test fails. Here it showed the golden vectors do not pin the check order (no vector has two faults), so a dedicated test now does.
- **Bytecode cache staleness**: Python reuses a `.pyc` when the source's mtime and size match, so a same-size edit within one second can run old code; clear `__pycache__` when mutation-testing.

## What the change did and how it was verified

`spi_protocol.py` gained `Sequencer` (thread-safe, skips zero, wraps), `process_sequencer()`, and `encode_command_reply` and `VersionInfo.encode` beside their decoders. `exchange.py` holds `Request`, `ExchangeSession` (`transact`, `exchange` with a required budget), `ExchangeResult` and `Outcome`, and `TransactionRecord` with four new fields at the end (`t1_request_sent_ns`, `t4_response_received_ns`, `request_received_local_us`, `raw_response`). `timing.py` keeps the statistics and a `TimingSession` adapter. `fake_backend.py` holds `FakeFirmware` and `FakeDataReady`. Documents: Issue #12 item 4 and sequencing step 5 amended, `SYSTEM_ARCHITECTURE.md` time path step 3 and SPI §13 aligned, Pi README "Exchange Session" section.

Checks on 2026-10-16 in the worktree: Pi tests 246 pass (212 before: +14 fake, +14 exchange, +6 Sequencer and encoders, one private-attribute test replaced by a `start_sequence` test); every golden vector reproduced byte for byte by the fake; `make_vectors.py --check` matches (13 vectors); HostTests 6 of 6; Debug build passes with the stack check; `doc_check` clean. The timing harness ran unchanged in `--fake` mode through the adapter; its CSV gained the four columns and `t4 - t1` equals `round_trip_ns` in the sampled row. Mutation checks: a changed identity fails two tests; swapping the sequence and message-type checks passed the vectors and is now caught by `test_sequence_checked_before_message_type`.

`/code-review medium` raised ten findings. Fixed: (1) the pending table is per session while sequences are process-wide, so the rule is now stated in `ExchangeSession`, the Issue #12 amendment and `SYSTEM_ARCHITECTURE.md`: one session owns a link and other consumers read its records; (2) T4 was set on every record, so T1, T4 and the round trip are now set together, only for a response that correlates to this session's pending table, and `t1_request_sent_ns is not None` is the observation test (tests for a foreign-request reply and for garbage); (3, 4) `TimingSession` as a subclass changed `transact`'s signature and the positional constructor order, so it is now a wrapper with its original constructor (positional-order test); (5) `SYSTEM_ARCHITECTURE.md` said T2 is recorded, now it says T2 waits for its wire placement and ClockSync is not yet implemented; (9) the fake imported the private `_is_newer`, now public as `is_newer_sequence`; (10) the new encoders raised `struct.error`, now `ValueError` like `SpiFrame`. Recorded, not fixed: (6) the adapter's empty default GET payload, because the GET payload rule is #88's (R1); (7) the always-empty `time_sync_*` columns, kept because the criteria keep the CSV fields, and #45 removes TIME_SYNC (now said in the record's docstring); (8) the older fakes remain by design until #102 (note wording corrected); (9, second half) the fakes live in `src/spi` on purpose, so the harness's `--fake` mode can use them (#102). Rechecked after the fixes: Pi tests 250 pass, `doc_check` clean, the harness ran in `--fake` mode through the wrapper.

## Open questions

- The golden vectors pin no validation order between two faults; a two-fault vector would pin it for the C side too (a candidate for #88, which next changes the vectors).
