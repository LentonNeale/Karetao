# CAN System Interface

## Authority

This document defines the Karetao system-level CAN contract. Arm Sensor Hub documentation defines the implementation of CAN services. MKS documentation remains external authority for MKS controller/protocol behaviour.

## System contract

- Nominal CAN rate: **1 Mbps** for v1 (SD-05).
- Identifier format: **standard 11-bit IDs** (SD-05).
- Average measured bus load target: **<50–60%** (SD-05).
- Logical joint, sensor and motor/CAN-ID mappings are deterministic and versioned, including direction, zero offset and transmission ratio (SD-07).
- CAN bus-off shall inhibit commands, perform bounded recovery, escalate after repeated failure and require explicit reactivation (SD-06).
- A CAN failure affecting motion scope must be evaluated against the machine risk assessment; SD-06 leaves joint-level versus whole-system stop scope open.
- Exact MKS controller model, firmware, command/feedback semantics, brake behaviour and physical configuration require target-hardware evidence (SD-05).

## Boundary

Karetao owns the system-level interface and integration requirements. The Arm Sensor Hub owns CanService/API, scheduler, queue and driver implementation. MKS/vendor documentation owns externally defined controller protocol behaviour.
