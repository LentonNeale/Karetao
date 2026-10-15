Origin: backlog story B130 (WP9, "S9.14 Exchange owner on the Pi: ExchangeSession with transact and exchange, one firmware-rules fake, process-wide Sequencer")

## Context

The harness, the probes, the snapshot logger and ClockSync each hand-roll a send, clock, correlate and pace loop, and five unshared fakes in `tests/spi` model the firmware differently. One module should own sending a request, clocking the transaction, correlating a reply that arrives in a later transaction and pacing the link, returning one record per transaction. Design settled with Lenton Neale on 2026-10-15 (architecture review, candidate 3).

## Scope

`RaspberryPi_Sensor_Hub/src/spi/exchange.py`, the fake, the Sequencer, and migrating the existing callers. Not covered: ClockSync itself, which is fed from the records by its owner.

## Acceptance Criteria

- [ ] `exchange.py` holds `ExchangeSession`, grown from `timing.TimingSession` (`TransactionRecord` keeps its name and CSV fields), and `spi_device.py` and `SpiDevice` are deleted
- [ ] `transact(request)` paces, clocks one transaction, records phase timings, decodes, correlates against the pending table and returns one `TransactionRecord`
- [ ] `exchange(request, filler=GET_STATUS, budget)` transacts the request then the filler until its reply correlates, a NACK correlates, or the budget is spent, and returns an outcome (replied, refused, exhausted) with the reply or NACK and the records consumed; firmware outcomes never raise
- [ ] `TransactionRecord` gains the Pi send time, `request_received_local_us` when present, the Pi receive time, and the raw response bytes when decoding fails; the session has no dependency on ClockSync
- [ ] A process-wide `Sequencer` in `spi_protocol.py` supplies sequences, and R3's single bounded jump on BAD_SEQUENCE lives there; two sessions in one process never both start from the seed
- [ ] `fake_backend.py` is one SpiBackend adapter enforcing the firmware rules (one-transaction reply delay, sequence high-water mark, BAD_STATE before activation, VERSION and SNAPSHOT replies, request CRC check, garbage mode); the five fakes are deleted and the probe and harness gain `--fake`
- [ ] The fake reproduces the shared golden vectors byte for byte (`test_fake_backend.py`)
- [ ] `spi_timing_harness.py`, `spi_link_probe.py` and `spi_time_sync_probe.py` are migrated, and `test_exchange.py` replaces `test_spi_device.py` and `test_timing.py`
- [ ] `RaspberryPi_Sensor_Hub/Documentation/README.md` names `exchange.py` as the owner of transaction, exchange and pacing
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Pi tests written against the fake: pipelined correlation, BAD_SEQUENCE and the R3 jump, BAD_STATE, budget and refused outcome, garbage with raw bytes, pacing by `FakeDataReady`.

## References

- `Documentation/01_SYSTEM/SYSTEM_OVERVIEW.md` (Vocabulary)
- `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (ruling R3)
