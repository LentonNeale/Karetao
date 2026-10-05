# Encoder bench procedure

## Purpose

This procedure produces one evidence record per fitted axis, five in total, offered against SYS-ENC-001: a valid reading that changes with motion, an STM32 timestamp, and the firmware identity from the `VERSION` message. Records follow [EVIDENCE_RECORD_FORMAT.md](EVIDENCE_RECORD_FORMAT.md). The fitted axes and mux channels are those in [SYSTEM_CONFIGURATION.md](../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) §2.1. The matrix row is in [SYSTEM_VERIFICATION_MATRIX.md](SYSTEM_VERIFICATION_MATRIX.md).

## Preconditions

- A clean Debug build is flashed from a commit whose `build_flags` bit 0 is clear.
- The Pi is at a known commit.
- The mux wiring matches §2.1.

## Steps

1. Run `python3 RaspberryPi_Sensor_Hub/tools/spi_link_probe.py --snapshot`, so the `VERSION` and sensor lines come from one run. From the `VERSION` line, note `git_hash_abbrev` and `dirty`. If `dirty=yes` (`build_flags` bit 0 set), stop: the record cannot satisfy a matrix row.
2. For each fitted axis (0, 1, 2, 4 and 5):
   1. Take a reading at rest.
   2. Move that joint, or for axes 4 and 5 that motor shaft, by hand.
   3. Take a second reading.
   4. Confirm SAMPLE_VALID is set on both readings, `raw_angle` differs, and `measurement_timestamp_us` increased.
3. In each record, note that axis 3 shows NOT_FITTED. This is an observation only.

Axes 4 and 5 are described only as motor-shaft raw angles.

## Record filing

File each record as `Documentation/05_VERIFICATION/evidence/<date>-enc-axis<N>.md` with this table. Records are not edited after acceptance.

| Field | Content |
|---|---|
| Date | YYYY-MM-DD |
| Requirement IDs | SYS-ENC-001 |
| Firmware identity | `git_hash_abbrev` and `dirty` (`build_flags` bit 0) from the probe's `VERSION` line; Pi commit hash |
| Hardware or rig | STM32 board, axis N, mux channel N+2, cable |
| Procedure | The steps above, with the probe command used |
| Result | Pass or fail: both readings valid, `raw_angle` differs, timestamp increased; the two readings and timestamps |
| Attachments | Probe output |
| Accepted by and date | Lenton Neale, date |
