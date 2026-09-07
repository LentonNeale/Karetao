# Multi-Sensor and TCA9548A Contract

**Status:** Design target  
**Owner:** SensorTask, TCA9548A driver, and AS5600 device layer  
**Boundary:** Six AS5600 devices -> sensor records/snapshots

## Target Topology

| Logical axis | TCA9548A channel | Sensor |
| ---: | ---: | --- |
| 0 | 0 | AS5600 |
| 1 | 1 | AS5600 |
| 2 | 2 | AS5600 |
| 3 | 3 | AS5600 |
| 4 | 4 | AS5600 |
| 5 | 5 | AS5600 |

The mapping is the commissioning default and must be configurable without changing the sensor algorithm. All AS5600 devices use the configured seven-bit device address unless a hardware revision requires otherwise.

## Sampling

The TCA9548A is sequential; samples are not simultaneous. A scan visits enabled channels in ascending logical-axis order, selects one mux channel, allows the required settle time, then performs the AS5600 transaction. The scan period, per-channel timeout, settle time, and maximum full-scan duration must be frozen before implementation.

Each successful measurement records acquisition time immediately after its bytes are received and decoded, using the shared 64-bit monotonic timestamp source. The timestamp spread across one snapshot must remain visible to the host.

The synchronized timestamp flag is valid only when the last accepted TIME_SYNC update is no older than five seconds. Otherwise the record remains usable as local-time data but must be marked unsynchronized.

The snapshot target is always six sensor records with logical IDs 0-5. A channel that is not ready or has failed remains represented with invalid/stale flags rather than changing record positions.

## Latest-Value Cache

SensorTask owns six `Sensor_LatestValue` records. Each contains stable logical joint and sensor identity, raw AS5600 counts, `processed_angle_mdeg`, status, validity flags, acquisition timestamp, synchronization quality, calibration version, freshness, and last-update timestamp. `processed_angle_mdeg` retains the current wire meaning; radians require a versioned payload-schema change.

After a successful AS5600 decode, the acquisition timestamp is captured through `TimeService_NowUs()`. SensorTask obtains synchronization quality from `TimeService_GetSyncSnapshot()` and marks the record synchronized only while time synchronization is valid. A failed read or magnet-status failure clears measurement fields and the sample-valid flag before publishing the record as invalid, so a stale reading is never presented as valid.

The cache is SensorTask-owned. Snapshot Builder may read the records through `SensorTask_GetLatestValues()` but must copy them into its own serialization buffer and must not mutate the cache. SPI serialization is outside this contract increment.

## Bring-Up

Configuration creates device records and validates channel/address uniqueness. Activation starts scan processing. Bring-up probes enabled channels individually and records per-channel availability. A failed channel does not automatically invalidate healthy channels.

Initial recommended policy:

- continue scanning healthy channels when one channel fails;
- mark failed channels invalid/stale;
- escalate the aggregate sensor service only when the configured minimum healthy-channel count is not met;
- expose per-channel fault and last-success timestamps.

The current firmware implements only channel 0 and must not claim six-channel support until all records and scan behavior exist.

## Runtime Failure

Classify a single timeout/NACK as a channel-local transient fault. Repeated failures may disable that channel for a bounded cool-down. A mux communication failure affects all channels and should escalate the sensor service to `ERROR` after the configured threshold.

Recovery re-probes the mux and disabled channels, returns the sensor service to `INACTIVE`, and requires explicit activation.

## Snapshot Relationship

A snapshot contains one stable record for each configured axis, including invalid records for unavailable channels. Snapshot ownership and buffer rules are defined in [SNAPSHOT_COHERENCY_CONTRACT.md](SNAPSHOT_COHERENCY_CONTRACT.md).

## Open Decisions

- scan rate and phase;
- mux settle delay;
- per-channel retry/cool-down;
- minimum healthy-channel count;
- startup partial-snapshot policy;
- mapping changes at runtime;
- whether sensor status reads and angle reads share one transaction.
