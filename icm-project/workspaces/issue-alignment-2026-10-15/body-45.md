## Context

The five gaps identified by the 2026-09-21 TIME_SYNC audit are moot under the Issue #12 clock-synchronization design (`Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`): the STM32 holds no offset, so there is nothing to apply to `frame_time_us` or `measurement_timestamp_us`, and the Pi does not initiate `TIME_SYNC`. Register item LIVE-19 lists this issue beside #42.

What remains here is the removal half of the implementation tracked in #42. This issue closes with that change.

## Scope

One lockstep change across `spi_protocol.c`, `spi_protocol.py` and their tests (ruling R16 in `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`):

- Remove STM32 `TIME_SYNC` (message 0x12) handling, the held offset and the `TimeService` sync state.
- Retire the sync-quality validity bits (sensor bit 5, motor bit 2 become reserved zero) and re-source health GREEN so it no longer needs sync.
- Remove the legacy Pi `TIME_SYNC` chain, including its drift check, and reshape the session and analysis code.
- Delete the two as-built TIME_SYNC documents with a provenance pointer to git history.

Not covered here: the new observation path (#42).

## Acceptance Criteria

- [ ] No symbol, message type, document row or test referring to TIME_SYNC, the held offset or the sync-quality bits remains on either side, apart from provenance lines.
- [ ] Health GREEN is reachable with no sync observation ever received.
- [ ] C encoder and Python decoder agree through the shared golden vectors after the removal.
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean; the task stack check passes.

## References

- `Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md`; `ARCHITECTURE_DECISIONS.md` rulings R16
- `Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` (TIME_SYNC marked deprecated); `Documentation/02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`
- Register item LIVE-19; implementation half: #42
