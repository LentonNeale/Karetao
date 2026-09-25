# Host System Interface

## Authority

This document defines the Karetao system-level host interface between the Raspberry-side integration and the rest of the system. Host implementation details remain Raspberry Sensor Hub authority.

## Contract

- Healthy Pi communication is required for motion permission. Any accepted, valid SPI message counts as liveness, so there is no separate heartbeat message. The STM32 count-based liveness check sets `link_stale`, which rejects motion. The trip thresholds `N_moving`/`N_idle` are open, and until they are set detection shall occur within **500 ms** (SD-03, Issue #12 item 11).
- The host/API authoritative joint representation is calibrated **radians**; changes to wire representation require explicit schema versioning (SD-12).
- Joint state exposes stable identity, position, available velocity, validity/status, acquisition timestamp, synchronization quality and calibration version (SD-13).
- The command interface provides commissioned position/velocity plus enable, disable and controlled-stop operations, with heartbeat, lifecycle, calibration and safety gating (SD-14).
- Calibration is computed on the Pi/workstation and transferred through a controlled validated configuration path (SD-10).
- Measurement history and estimator history are owned on the Raspberry/EKF side; STM32 provides bounded latest-value/coherent records (SD-09).

## Motion-permission integration

Pi link liveness is one prerequisite of the proposed system-level normal-motion gate, and a live link does not by itself grant motion permission. When `link_stale` trips, the STM32 motion gate fails closed. New motion commands are rejected, and the approved SD-03 controlled-stop/motor-disable response starts where the transport remains usable. The last motion command is never held.

## Open integration definitions

Command acknowledgement/freshness semantics, exact timeout/cancellation rules, and final motion-permission ownership remain open items in the decision records.
