# System Configuration

## Authority

This document is the authoritative Karetao destination for system-level controlled configuration. Component-specific build/toolchain, driver, and implementation configuration remains component authority.

---

## 1. Physical Interface Configuration

- **CAN nominal rate:** **1 Mbps** for v1, standard 11-bit IDs (SD-05).
- **SPI initial maximum:** **5 MHz**, pending target-system validation (SD-01, SD-15).
- **SPI framing:** 512-byte frame, maximum 490-byte payload, Mode 0, little-endian, CRC-32/ISO-HDLC (SD-15).
- **Clock sync:** observation on every applicable SPI exchange; invalid after 5 s without an accepted observation (SD-19, Issue #12).
- **Pi link liveness:** count-based (`N_moving` < `N_idle`, values open); interim detection limit 500 ms (SYS-FAIL-001).
- **`counter_extension_gap_us`:** fixed 500 ms TIM2 wrap-extension guard, to be reviewed after hardware characterization (Issue #12 item 11).

---

## 2. Joint, Sensor, and Motor Mapping

**Schema version:** 1 (current). **Status:** Approved implementation baseline.

The mapping model defines a one-to-one relationship between:
- Logical joint identity (0–5 for six axes)
- AS5600 sensor identity (I2C channel and sensor select)
- Motor index (0–7)
- CAN motor ID (11-bit standard CAN identifier)
- Direction convention (`+1` or `−1`)
- Zero offset (millidegrees)
- Transmission ratio (numerator/denominator)

**Schema v1 capabilities:**
- One-to-one logical joint ↔ sensor ↔ motor mapping.
- Supports logical joints 0–5, AS5600 sensors 0–5, motor indices 0–7, standard 11-bit CAN IDs.
- Direction and transmission-ratio scaling for each joint.

**Schema v1 limitations:**
- **Does not represent differential, coupled, or multi-motor joints.** Those topologies require a new schema version and explicit semantics; they must not be encoded as multiple v1 records for one logical joint (SD-26, SYS-MECH-001).

**Validation and activation:**
- Configuration is validated before activation.
- `JointMapping_Validate()` rejects unsupported schema versions, invalid IDs, invalid direction, zero transmission-ratio components, and duplicate assignments.
- A failed mapping blocks CAN registration and CAN/SensorTask activation; I2C and SPI remain available for fault reporting.
- SensorTask uses the validated record's logical joint and AS5600 IDs to keep latest-value records at stable positions.
- Future MotorService uses the matching logical joint, motor index, CAN ID, direction, offset, and transmission ratio when translating logical commands and feedback.

**Current status:**
- Single-entry mapping reflects existing bring-up registration only.
- Full commissioning of the complete physical mapping is required before energized-motion release.

---

## 3. Calibration Data

**Schema version:** 1 (current). **Status:** Approved implementation baseline.

The calibration model is versioned and integrity-protected.

**Record structure:**
- Schema version, logical sensor and joint identity
- Zero offset (millidegrees), scale (parts per million)
- Direction (`−1` or `+1`), generation number
- CRC-32/ISO-HDLC value (covering record fields, excluding CRC and validity marker)
- Validity marker

**Current capabilities:**
- Supports logical IDs 0–5.
- Supports nonzero scale and direction `−1` or `+1`.
- Generation number supports modulo-32-bit ordering for redundant record selection.

**Ownership:**
- Calibration is computed offline on the Raspberry Pi or engineering workstation.
- The STM32 does not estimate or modify calibration parameters.
- STM32 validates received or loaded records, applies only a selected valid record, and reports active schema version and generation.

**Validation and selection:**
- Reject null, unsupported-schema, malformed identity/parameter, zero-generation, invalid-marker, and CRC-mismatched records.
- Reject duplicate sensor/joint identities in one active configuration set.
- For redundant records of the same identity, validate both and select the newer generation using modulo-32-bit ordering.
- Reject equal generations for redundant records as ambiguous.
- Do not select an older or corrupted fallback record when candidate validation fails.
- `Calibration_ActiveVersion` reports the selected record, schema version, and generation.

**Redundancy:**
- The system stores redundant copies in STM32 flash slots.
- A host-side source copy is maintained and synchronized.
- Flash slot placement, write ordering, and power-loss handling are component concerns (not system configuration).

---

## 4. System Time Representation

- **Host/API authoritative joint representation:** Calibrated radians (SD-12).
- **STM32 internal time domain:** Monotonic local time in microseconds only; the STM32 holds no offset (Issue #12).
- **Timestamp acquisition:** Measurement timestamps captured immediately after successful sensor read/decode, in STM32 local time, then converted to Pi time by ClockSync.
- **Synchronization quality:** Timestamps marked `SYNCHRONIZED` while `ClockSync.is_valid()` (last accepted observation less than 5 seconds old); otherwise marked `UNSYNCHRONIZED`.

---

## 5. Joint Angle Numeric Representation

- **Canonical unit:** radians.
- **Normal external decimal precision:** **4 decimal places** (`0.0001 rad`, approximately `0.00573°`).
- **AS5600 nominal resolution:** 12-bit, 4096 codes/revolution, approximately `0.001534 rad` per code.
- **Raw representation:** Raw AS5600 counts remain available diagnostically.
- **Internal calculation precision:** Firmware/host calculations may retain greater floating-point precision where required for filtering, interpolation, or derivative calculations.
- **Interpretation:** The four-decimal choice is a software representation requirement. It must not be interpreted as a claim that the physical joint angle is accurate to `0.0001 rad`.
- **Wire-format constraint:** The current processed-millidegree wire field must not be silently reinterpreted as radians. A versioned schema change and documented conversion are required before the wire representation changes, as specified by SD-12.
- **Supporting engineering reference:** `Arm_Sensor_Hub/Documentation/AS5600_PRECISION_AND_ACCURACY.md`.

## 6. Configuration Authority Boundary

Concrete STM32 build/toolchain settings, driver settings, Raspberry provisioning, and component-specific configuration are not system configuration authority and remain in the component repositories.

**Provisional values:** Values marked provisional or validation-dependent (5 MHz SPI, 1 Mbps CAN, ±1 ms timestamp error, 500 Hz EKF) must not be represented as final release configuration until the corresponding integration evidence is accepted.

---

## Provenance

Reconciled from `docs/project/firmware/JOINT_MAPPING_CONTRACT.md` (joint/sensor/motor mapping schema, validation, and current status) and `docs/project/firmware/CALIBRATION_CONTRACT.md` (calibration record model, ownership, validation, redundancy, and integration work). All caveats preserved verbatim: schema v1 cannot represent differential end effectors (SYS-MECH-001); redundant selection requires modulo-32-bit ordering; calibration is offline-computed, never on-device; commissioning validation required before motion release.
