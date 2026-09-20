# Host System Interface

## Authority

This document defines the Karetao system-level host interface between the Raspberry-side integration and the rest of the system. Host implementation details remain Raspberry Sensor Hub authority.

## Contract

- Raspberry Pi heartbeat is required for motion permission; a **500 ms** heartbeat timeout causes motion rejection (SD-03).
- The host/API authoritative joint representation is calibrated **radians**; changes to wire representation require explicit schema versioning (SD-12).
- Joint state exposes stable identity, position, available velocity, validity/status, acquisition timestamp, synchronization quality and calibration version (SD-13).
- The command interface provides commissioned position/velocity plus enable, disable and controlled-stop operations, with heartbeat, lifecycle, calibration and safety gating (SD-14).
- Calibration is computed on the Pi/workstation and transferred through a controlled validated configuration path (SD-10).
- Measurement history and estimator history are owned on the Raspberry/EKF side; STM32 provides bounded latest-value/coherent records (SD-09).

## Open integration definitions

Command acknowledgement/freshness semantics, exact timeout/cancellation rules, and final motion-permission ownership remain open items in the decision records.
