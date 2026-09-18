# Karetao Documentation Authority Model

## Authority hierarchy

| Level | Authority | Scope |
|---|---|---|
| L0 | `LentonNeale/Karetao` | System requirements and system architecture |
| L1 | Component repository | Component implementation |
| L2 | Vendor/external specification | External equipment and protocols |
| L3 | Verification evidence | Demonstration of compliance |

The levels describe authority by subject. They are not a general precedence rule in which every L0 document overrides every L1-L3 document. Conflict resolution is determined by the subject being documented.

## Karetao authority

Karetao is authoritative for:

- what the system must do;
- system architecture;
- system-level interfaces;
- system timing;
- system synchronization;
- system safety;
- system configuration requirements;
- system-level verification requirements;
- system integration requirements.

A component repository cannot redefine these requirements.

## Component authority

A component repository is authoritative for implementation-specific information, including:

- component architecture;
- implementation data flow;
- firmware/software behavior;
- implementation configuration;
- hardware-specific constraints;
- drivers;
- implementation timing;
- implementation diagnostics;
- component verification.

Component documentation must not silently redefine a Karetao system requirement.

For Karetao, the currently defined component authorities are:

- Arm Sensor Hub — `LentonNeale/Arm_Sensor_Hub`
- Raspberry Sensor Hub — `LentonNeale/Raspberry_Sensor_Hub`

## External authority

Vendor documentation is authoritative for the behavior of the vendor equipment or protocol it describes.

For example, MKS documentation is authoritative for MKS controller behavior.

Vendor documentation does not define Karetao system requirements.

## Verification authority

Verification records provide evidence that requirements or implementation behavior have been demonstrated.

Evidence does not redefine the requirement.

A component implementation being verified does not automatically mean the Karetao system requirement has been system-verified.

## Conflict resolution

When documentation conflicts:

1. Identify the subject of the conflict.
2. Identify the authority responsible for that subject.
3. Use the authoritative source for that subject.
4. Treat lower-level documentation as implementation/reference material.
5. Record unresolved conflicts explicitly.
6. Never silently create a new interpretation.

Where the conflict is between a system requirement and an implementation description, the system requirement remains authoritative for the system obligation. The implementation document must be corrected, or the system requirement must be formally changed through Karetao change control.

Where an external specification conflicts with a Karetao requirement, the documents describe different authorities: the external source governs the external equipment or protocol, while Karetao governs the required system behaviour. The resulting incompatibility must be recorded and resolved; neither source silently overrides the other outside its scope.

## Core rule

> A lower-level document may explain how a higher-level requirement is implemented, but it must not redefine the higher-level requirement.
