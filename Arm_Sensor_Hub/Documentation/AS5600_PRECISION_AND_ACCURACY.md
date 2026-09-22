# AS5600 Angle Precision and Accuracy

**Status:** Engineering reference  
**Scope:** AS5600 magnetic angle sensing used by the Arm Sensor Hub  
**Authority:** Supporting engineering analysis; the AS5600 datasheet remains the authority for device specifications.

## Purpose

This note separates the AS5600's **numeric resolution**, **physical measurement accuracy**, and **software representation precision**. These are distinct properties and must not be treated as interchangeable.

## Resolution

The AS5600 provides a 12-bit angular output:

- 4096 codes per 360° rotation.
- One code corresponds to approximately **0.08789°**.
- In radians, one code corresponds to approximately **0.001534 rad**.

This is the sensor's nominal quantisation resolution. It does not mean that the physical shaft angle is accurate to one count under all mechanical and magnetic conditions.

## Measurement Accuracy

Real-world angle accuracy is affected by the magnetic and mechanical installation.

Relevant error sources include:

- Magnet centring and axial alignment.
- Magnet-to-sensor air gap.
- Magnet type and magnetic field strength.
- Mechanical runout and joint compliance.
- Temperature and other environmental effects.
- Sensor operating conditions and magnetic-field diagnostics.

Published/vendor accuracy figures should therefore be treated separately from the 12-bit output resolution. Retaining additional decimal places in software does **not** create equivalent physical measurement accuracy.

## Numeric Representation

For Karetao, the canonical host/API representation is calibrated radians.

The recommended representation precision is:

| Decimal places | Increment | Approx. degrees | Interpretation |
|---|---:|---:|---|
| 3 | 0.001 rad | 0.0573° | Too coarse for the intended representation; it discards useful native sensor resolution. |
| **4** | **0.0001 rad** | **0.00573°** | **Recommended representation precision.** Provides finer numeric granularity than one AS5600 count without implying equivalent physical accuracy. |
| 5 | 0.00001 rad | 0.000573° | May be retained internally where filtering or derivative calculations benefit from additional numerical granularity, but should not be interpreted as sensor accuracy. |

### Recommended Karetao policy

- Use **calibrated radians** as the authoritative host/API representation.
- Use **4 decimal places** as the normal external numeric representation where decimal formatting is required.
- Retain raw AS5600 counts diagnostically.
- Internal calculations may retain more floating-point precision where required by filtering, interpolation, or derivative calculations.
- Do not describe the chosen decimal precision as the sensor's measurement accuracy.

## Mechanical Installation Considerations

The achievable physical accuracy depends strongly on the installation.

### Magnet alignment

The magnet should be centred over the sensing element. Off-axis placement can introduce angular non-linearity.

### Air gap

The magnet-to-sensor spacing must remain within the device/application's specified operating range. The exact acceptable range should be taken from the applicable AS5600 datasheet and magnet configuration rather than treated as a universal mechanical constant.

### Magnetic field strength

The AS5600 provides magnetic-field diagnostics including AGC. Commissioning should use these diagnostics to identify unsuitable magnetic coupling.

The firmware already exposes AS5600 status information; commissioning evidence should record the observed magnetic-field condition alongside angle measurements.

## Verification Implications

The 4-decimal representation is a **software representation requirement**, not a verified sensor-accuracy requirement.

Physical validation should separately establish:

1. Quantisation behaviour across the usable joint range.
2. Static repeatability at representative joint positions.
3. Accuracy against an independent angular reference.
4. Sensitivity to magnet alignment and air gap.
5. Behaviour under the expected mechanical load.
6. Any filtering/derivative behaviour that motivates retaining more internal numerical precision.

Measured results should be recorded under `Documentation/05_VERIFICATION/` once target-hardware testing is performed.

## Relationship to System Configuration

The system-level canonical representation is defined in:

- `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md`
- SD-12 — Authoritative Angle Representation

This document provides the engineering rationale and AS5600-specific constraints; it does not replace the system configuration or interface contracts.
