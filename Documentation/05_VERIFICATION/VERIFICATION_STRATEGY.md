# Verification Strategy

## Authority

This document defines the Karetao system verification strategy. Component repositories define and execute component-level verification; Karetao determines whether integrated evidence establishes system verification.

## Verification chain

System requirement -> responsible component(s) -> component implementation -> component verification -> integration verification -> Karetao system verification.

Each stage must retain evidence appropriate to its scope.

## Verification classes

| Class | Purpose | Does it establish SYSTEM_VERIFIED? |
|---|---|---|
| Component verification | Demonstrates implementation behaviour within component scope | No |
| Hardware verification | Demonstrates behaviour against target hardware | No, not by itself |
| Integration verification | Demonstrates interaction between system components | Only when accepted against the relevant system requirement |
| System verification | Demonstrates accepted integrated system behaviour | Yes, when formally accepted |

## Required system verification areas

At minimum, the system verification process must address timing and synchronization; Raspberry heartbeat and communication-loss response; motor feedback freshness and escalation; CAN interface, load and bus-off recovery; joint/state mapping; SPI framing, CRC, ownership, timing and physical-layer behaviour; host command/state interface; calibration and controlled configuration; fault/recovery and motion gating; and independent safety mechanisms.

## Acceptance rule

SYSTEM_VERIFIED shall only be assigned after the relevant integrated evidence is accepted through the Karetao system verification process.

Component VERIFIED or HARDWARE_VERIFIED status must not be copied into the system verification matrix as system acceptance.

## Provenance

Reconciled from the framework verification model, the audited documentation classification, and the existing system verification matrix.
