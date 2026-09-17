# Calibration Record Contract

**Status:** Approved implementation baseline
**Owner:** Application configuration service
**Boundary:** Pi/workstation calibration output -> validated STM32 calibration parameters

## Ownership

Calibration is computed offline on the Raspberry Pi or an engineering workstation. The STM32 does not estimate or modify calibration parameters. It validates received or loaded records, applies only a selected valid record, and reports the active schema version and generation.

## Record Model

`Calibration_Record` is a versioned logical record containing schema version, logical sensor and joint identity, zero offset in millidegrees, scale in parts per million, direction, generation, CRC-32 value, and validity marker. The current schema supports logical IDs 0 through 5, nonzero scale, and direction `-1` or `1`.

The CRC field is checked against a caller-supplied CRC calculated from the canonical schema serialization. The CRC field and validity marker are excluded from that coverage. The shared CRC-32/ISO-HDLC helper is owned by Task 13; this validation layer does not create a second CRC implementation or rely on native C structure layout.

## Validation and Selection

- Reject null, unsupported-schema, malformed identity/parameter, zero-generation, invalid-marker, and CRC-mismatched records.
- Reject duplicate sensor/joint identities in one active configuration set.
- For two redundant records of the same identity, validate both and select the newer non-equal generation using modulo-32-bit ordering.
- Reject equal generations for redundant records as ambiguous.
- Do not select an older or corrupted fallback record when a candidate validation operation fails.

`Calibration_ActiveVersion` reports the selected record, schema version, and generation. Flash slot placement, write ordering, and power-loss handling are intentionally excluded.

## Open Integration Work

- Define canonical serialization and connect CRC validation to the shared CRC-32/ISO-HDLC helper.
- Define redundant flash-slot allocation, erase/write sequencing, endurance budget, and power-loss recovery evidence.
- Bind validated calibration sets to versioned joint/sensor mappings and lifecycle activation prerequisites.