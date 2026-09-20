# System Architecture

## Authority

This document is the Karetao system-level architecture authority. It describes the integrated system structure and responsibilities, not component implementation details.

## System structure

Karetao integrates:

1. **Arm Sensor Hub** — STM32-based hardware-facing control and sensor component.
2. **Raspberry Sensor Hub** — Raspberry Pi host-side integration component.
3. **ROS 2 / estimation / control / planning** — host-side system functions.
4. **External motor/controller equipment** — externally defined equipment and protocol behaviour.
5. **Independent safety functions** — safety mechanisms whose independence and boundary are determined by the machine risk assessment and safety architecture.

The architectural boundary is:

```
Karetao system
├── Raspberry Sensor Hub / host integration
│   ├── measurement history / estimator integration
│   ├── system command and state interfaces
│   └── ROS 2 integration
├── Arm Sensor Hub
│   ├── sensor acquisition
│   ├── actuator-facing services
│   └── system interface implementation
├── External MKS/controller equipment
└── Independent safety path
```

## Responsibility model

Karetao owns the system requirements, system interfaces, timing/synchronization rules, integration constraints, safety requirements and component roles.

Arm Sensor Hub owns implementation of its assigned STM32 services and hardware-facing behaviour.

Raspberry Sensor Hub owns implementation of its host-side integration.

External vendors define the behaviour of their equipment and protocols.

## Data and control flow

At system level:

1. Sensors are acquired by the Arm Sensor Hub.
2. Timestamped/coherent state is exposed through the system interfaces.
3. Raspberry-side integration owns estimator history and system-level host processing.
4. Commands flow from host/system control toward the Arm Sensor Hub and external actuator interface.
5. Fault, freshness, lifecycle, synchronization and safety gates constrain motion permission.
6. Recovery returns the system to an explicitly reactivated state and must not silently resume motion.

The exact service APIs, DMA ownership, scheduler details and codec implementation remain component documentation.

## Architectural decisions and constraints

- 100 Hz is the baseline sensor/state publication and initial control-loop rate; the current EKF setting is 500 Hz subject to integration constraints (SD-01).
- The approximately 46 ms six-axis physical sweep is not itself a 500 Hz full-sweep rate; estimator behaviour therefore depends on timestamped/latest-value handling (SD-01, SD-08).
- The differential end effector requires an explicit motor-to-DOF transformation (SD-26, proposed).
- System-level motion permission must be a defined authority rather than an emergent property of individual component state machines (SD-02, SD-23).
- Independent safety functions remain distinct from application controlled-stop behaviour (SD-25).

## Legacy source reconciliation

The former `docs/project/system/architecture.md` was mixed system architecture/component implementation content. Its system-level structure is represented here; concrete STM32 service/API and codec details remain component-owned and are not copied wholesale.
