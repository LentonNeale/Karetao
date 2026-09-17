# Joint/Sensor/Motor Mapping Contract

**Status:** Approved implementation baseline
**Owner:** Application configuration service
**Boundary:** Logical joint identity -> AS5600 sensor identity and CAN motor identity

## Mapping Model

Schema version 1 defines a one-to-one `JointMapping_Record` containing logical joint ID, AS5600 sensor ID, motor index, CAN ID, direction, zero offset in millidegrees, and a positive transmission-ratio numerator and denominator. It supports logical joints and AS5600 IDs 0 through 5, motor indices 0 through 7, and standard 11-bit CAN IDs.

The mapping does not represent differential, coupled, or multi-motor joints. Those topologies require a new schema version and explicit semantics; they must not be encoded as multiple v1 records for one logical joint.

## Validation and Activation

`JointMapping_Validate()` rejects unsupported schema versions, invalid IDs, invalid direction, zero transmission-ratio components, and duplicate logical-joint, sensor, motor-index, or CAN-ID assignments. `JointMapping_FindByJoint()` exposes stable identity metadata only after a mapping has passed validation.

Application initialization validates its configured mapping before normal service activation. A failed mapping blocks CAN registration and CAN/SensorTask activation; I2C and SPI may remain available for fault reporting. The current single-entry mapping reflects existing bring-up registration only and is not final physical commissioning data.

## Consumer Ownership

- SensorTask uses the validated record's logical joint and AS5600 sensor IDs to keep latest-value records at stable positions.
- Future MotorService uses the matching logical joint, motor index, CAN ID, direction, zero offset, and transmission ratio when translating logical commands and feedback to `CanService` operations.
- Calibration records supply calibration parameters only; they do not redefine transport identity or mapping topology.

## Open Integration Work

- Commission and validate the complete physical mapping before energized-motion release.
- Bind mapping selection to persisted calibration validation and explicit lifecycle prerequisites.
- Define a future schema for mechanically coupled or differential joints.