# Component Documentation Integration Model

This document defines the documentation contract that component repositories must eventually follow when integrating with Karetao. It does not modify component repositories.

## Component Repository Template

Each component repository should eventually use a structure similar to:

```text
Documentation/
├── 00_INDEX.md
├── 01_ARCHITECTURE/
├── 02_INTERFACES/
├── 03_COMPONENT/
├── 04_EXTERNAL/
├── 05_CONFIGURATION/
├── 06_SAFETY/
├── 07_VERIFICATION/
├── 08_DEVELOPMENT/
└── 99_ARCHIVE/
```

The exact contents may vary by component.

## Authority Declaration

Each component repository should eventually contain `Documentation/00_DOCUMENTATION_AUTHORITY.md` identifying the repository, component, component documentation authority, Karetao system authority, and relevant external authorities.

## Traceability

Component documentation should reference system requirements by their Karetao identifier. Do not copy the complete system requirement into the component repository.

## Interface Relationship

Karetao defines the system interface. The component repository defines the implementation of that interface.

## Verification Relationship

Karetao owns system-level verification. A component repository may provide implementation evidence. Component evidence must not automatically be represented as system verification.

## External Documentation

Vendor documentation remains external authority. Component documents may reference vendor manuals but must distinguish vendor behavior, system requirement, and component implementation.

## Status

Where appropriate, component documentation should distinguish SPECIFIED, IMPLEMENTED, VERIFIED, HARDWARE_VERIFIED, SYSTEM_VERIFIED, RELEASED, SUPERSEDED, DEFERRED, and BLOCKED. SYSTEM_VERIFIED is a system-level status and must not be claimed solely because component testing passed.

## Integration Principle

Karetao = system authority.

Component repository = implementation authority.

Vendor documentation = external authority.

Verification = evidence.
