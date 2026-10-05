# System Configuration

## Authority

This document is the authoritative Karetao destination for system-level controlled configuration. Component-specific build/toolchain, driver, and implementation configuration remains component authority.

Tunable and physical values are referenced by PRM ID; their working values and bases are in [`PARAMETER_REGISTER.md`](PARAMETER_REGISTER.md).

---

## 1. Physical Interface Configuration

Physical and tunable values (CAN bit rate, SPI clock ceiling, clock-sync validity window, Pi link liveness, counter extension gap) are held in [`PARAMETER_REGISTER.md`](PARAMETER_REGISTER.md), each with a basis. The former list maps to the register as follows: CAN rate to PRM-CAN-01 (standard 11-bit IDs, SD-05); SPI maximum to PRM-SPI-01 (SD-01, SD-15); SPI framing (512-byte frame, maximum 490-byte payload, Mode 0, little-endian, CRC-32/ISO-HDLC) stays a contract constant in [`SPI_SYSTEM_INTERFACE.md`](../02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md); clock-sync validity to PRM-TS-03 (SD-19, Issue #12); Pi link liveness to PRM-LINK-01 and PRM-LINK-02 (SYS-FAIL-001); `counter_extension_gap_us` to PRM-TS-04 (Issue #12 item 11).

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

**Schema v1 limitations (deferred by the charter until the hardware exists):**
- **Does not represent differential, coupled, or multi-motor joints (deferred by the charter).** Those topologies require a new schema version and explicit semantics; they must not be encoded as multiple v1 records for one logical joint (SD-26, SYS-MECH-001).

**Validation and activation:**
- Configuration is validated before activation.
- `JointMapping_Validate()` rejects unsupported schema versions, invalid IDs, invalid direction, zero transmission-ratio components, and duplicate assignments.
- A failed mapping blocks CAN registration and CAN/SensorTask activation; I2C and SPI remain available for fault reporting.
- SensorTask uses the validated record's logical joint and AS5600 IDs to keep latest-value records at stable positions.
- Future MotorService uses the matching logical joint, motor index, CAN ID, direction, offset, and transmission ratio when translating logical commands and feedback.

### 2.1 Commissioning table (as built, 2026-09-17; recorded 2026-10-03; joint names and encoders fitted 2026-10-04)

This table is the only statement of which axes carry an encoder, which TCA9548A channel each uses and which MKS motor each maps to (SYS-ENC-003). The tables in `Arm_Sensor_Hub/App/Src/app_init.c` implement it and must match it; a mismatch is a defect in whichever side was changed without the other.

| Axis (logical ID) | Joint name | Encoder fitted | Mux channel | Motor index | CAN ID | MKS model | MKS firmware | Direction | Zero offset | Ratio | Basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Joint X | yes | 2 | 0 | 0x001 | SERVO42 (CAN_SERVICE_MKS_SERVO42) | unknown | +1 | 0 | 1/1 | as built (app_init.c); joint name and encoder fitted: commissioning fact, Lenton Neale 2026-10-04 |
| 1 | Joint Y | yes | 3 | none registered | none registered | none registered | unknown | none registered | none registered | none registered | as built (app_init.c); joint name and encoder fitted: commissioning fact, Lenton Neale 2026-10-04 |
| 2 | Joint Z | yes | 4 | none registered | none registered | none registered | unknown | none registered | none registered | none registered | as built (app_init.c); joint name and encoder fitted: commissioning fact, Lenton Neale 2026-10-04 |
| 3 | Wrist Joint 1 | no | 5 | none registered | none registered | none registered | unknown | none registered | none registered | none registered | as built (app_init.c); joint name and encoder fitted: commissioning fact, Lenton Neale 2026-10-04 |
| 4 | Differential Motor 1 | yes | 6 | none registered | none registered | none registered | unknown | none registered | none registered | none registered | as built (app_init.c); joint name and encoder fitted: commissioning fact, Lenton Neale 2026-10-04; coupled-joint meaning deferred (SD-26) |
| 5 | Differential Motor 2 | yes | 7 | none registered | none registered | none registered | unknown | none registered | none registered | none registered | as built (app_init.c); joint name and encoder fitted: commissioning fact, Lenton Neale 2026-10-04; coupled-joint meaning deferred (SD-26) |

Logical axis N maps to mux channel N+2. Channel SD0 carries the bench sensor and is excluded; SD1 is unpopulated.

Axes 4 and 5 report the raw angle of each motor shaft; no end-effector or coupled-joint meaning is given (SD-26 deferred).

The Encoder fitted column is implemented by `s_sensor_encoder_fitted` in `Arm_Sensor_Hub/App/Src/app_init.c`. An axis marked no is published as NOT_FITTED (validity bit 6) and is never a fault (SYS-ENC-002). Cells still marked unknown are facts only the maintainer can supply; they are filled in the sprint that needs them.

Full commissioning is required before gated motion on an axis (charter goal 4).

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

**Evidence required before gated motion** (matrix row SYS-CAL-001): versioning, CRC, redundancy, power-loss handling and the host copy.

**Redundancy:**
- The system stores redundant copies in STM32 flash slots.
- A host-side source copy is maintained and synchronized.
- Flash slot placement, write ordering, and power-loss handling are component concerns (not system configuration).

---

## 4. System Time Representation

- **Host/API authoritative joint representation:** Calibrated radians (SD-12).
- **STM32 internal time domain:** Monotonic local time in microseconds only; the STM32 holds no offset (Issue #12).
- **Timestamp acquisition:** Measurement timestamps captured immediately after successful sensor read/decode, in STM32 local time, then converted to Pi time by ClockSync.
- **Synchronization quality:** Timestamps marked `SYNCHRONIZED` while `ClockSync.is_valid()` (last accepted observation within PRM-TS-03); otherwise marked `UNSYNCHRONIZED`.

---

## 5. Joint Angle Numeric Representation

- **Canonical unit:** radians.
- **Normal external decimal precision:** PRM-REP-01.
- **AS5600 nominal resolution:** PRM-ACQ-06.
- **Raw representation:** Raw AS5600 counts remain available diagnostically.
- **Internal calculation precision:** Firmware/host calculations may retain greater floating-point precision where required for filtering, interpolation, or derivative calculations.
- **Interpretation:** The four-decimal choice is a software representation requirement. It must not be interpreted as a claim that the physical joint angle is accurate to the precision in PRM-REP-01.
- **Wire-format constraint:** The current processed-millidegree wire field must not be silently reinterpreted as radians. A versioned schema change and documented conversion are required before the wire representation changes, as specified by SD-12.
- **Supporting engineering reference:** `Arm_Sensor_Hub/Documentation/AS5600_PRECISION_AND_ACCURACY.md`.

## 6. Configuration Authority Boundary

Concrete STM32 build/toolchain settings, driver settings, Raspberry provisioning, and component-specific configuration are not system configuration authority and remain in the component repositories.

**Provisional values:** Values are Provisional until the register links evidence; see the register's basis column. They must not be represented as final release configuration, and they are not restated here.

---

## Provenance

Reconciled from `docs/project/firmware/JOINT_MAPPING_CONTRACT.md` (joint/sensor/motor mapping schema, validation, and current status) and `docs/project/firmware/CALIBRATION_CONTRACT.md` (calibration record model, ownership, validation, redundancy, and integration work). All caveats preserved verbatim: schema v1 cannot represent differential end effectors (SYS-MECH-001); redundant selection requires modulo-32-bit ordering; calibration is offline-computed, never on-device; evidence required before gated motion (matrix row SYS-CAL-001).
