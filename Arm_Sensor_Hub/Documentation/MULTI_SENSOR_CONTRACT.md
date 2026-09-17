# Multi-Sensor and TCA9548A Contract

**Status:** Design target with commissioned implementation evidence  
**Owner:** SensorTask, TCA9548A driver, and AS5600 device layer  
**Boundary:** Six AS5600 devices -> sensor records/snapshots

## Target Topology

| Logical axis | TCA9548A channel | Sensor |
| ---: | ---: | --- |
| 0 | 2 | AS5600 |
| 1 | 3 | AS5600 |
| 2 | 4 | AS5600 |
| 3 | 5 | AS5600 |
| 4 | 6 | AS5600 |
| 5 | 7 | AS5600 |

The table above is the commissioned SD2-SD7 mapping. The mapping remains configurable without changing the sensor algorithm. All AS5600 devices use the configured seven-bit device address unless a hardware revision requires otherwise.

Channels 0 and 1 are deliberately outside the published axis set. Channel 0 carries a bench test sensor and channel 1 is unpopulated in the earlier bench configuration, so neither appears in a snapshot; a seventh record cannot be published without a payload-schema change.

The configurability requirement is implemented in code: `SensorTask_ConfigureMuxChannels()` binds each axis to its channel, validating the whole map before applying any of it, and rejecting a map that is the wrong size, names a channel above 7, repeats a channel, or arrives while the service is `ACTIVE`. The binding lives in one table in `App/Src/app_init.c`, and `App_Start()` refuses sensor activation when the map was rejected. Record positions and logical IDs remain 0-5 regardless of which channels are bound.

## Sampling

The TCA9548A is sequential; samples are not simultaneous. A scan visits enabled channels in ascending logical-axis order, selects one mux channel, allows the required settle time, then performs the AS5600 transaction. The scan period, per-channel timeout, settle time, and maximum full-scan duration must be frozen before treating the current scheduler timing as an accepted scan contract.

Each successful measurement records acquisition time immediately after its bytes are received and decoded, using the shared 64-bit monotonic timestamp source. The timestamp spread across one snapshot must remain visible to the host.

The synchronized timestamp flag is valid only when the last accepted TIME_SYNC update is no older than five seconds. Otherwise the record remains usable as local-time data but must be marked unsynchronized.

The snapshot target is always six sensor records with logical IDs 0-5. A channel that is not ready or has failed remains represented with invalid/stale flags rather than changing record positions.

The current firmware sweeps all six logical axes in one blocking pass per 20 ms scheduler tick. The measured full six-axis sweep is approximately 46 ms, so the 20 ms value is a scheduler period and must not be described as a demonstrated 20 ms full-scan completion time. The scan period, settle time, per-channel timeout, and minimum healthy-channel threshold remain unfrozen.

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

## Commissioning Evidence

On 2026-09-17 the current implementation was run on a physical STM32F405 with the commissioned logical mapping bound to SD2-SD7. All six commissioned axes produced valid magnet samples with zero communication or magnet errors during the commissioning run. This is evidence for the six-axis commissioned mapping and sensor-path behavior at the recorded bench conditions; it is not evidence that the unfrozen scan timing parameters meet any separate 20 ms full-scan requirement.

An earlier bench run used one real AS5600 on channel 0 with channels 1-5 unwired. That run demonstrated isolated communication failures for absent channels and a real status/angle read from the wired channel, but it is not the evidence basis for the commissioned SD2-SD7 mapping. The earlier run also recorded a magnet-too-weak status and a later loss of successful reads; those observations remain bench evidence rather than a six-axis acceptance result.

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
