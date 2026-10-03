# System Lifecycle

**Purpose:** Define the lifecycle vocabulary and state machine that controls subsystem readiness, safety gating, and recovery across the Karetao system.

The Karetao system uses a canonical four-state lifecycle inspired by ROS 2 Managed Nodes, implemented as a simple state machine in the STM32 firmware. Lifecycle state controls readiness and safety; it does not replace peripheral state machines or internal states.

## 1. Canonical States

| State | Meaning |
| --- | --- |
| **UNCONFIGURED** | Required configuration or resources are not ready. Normal operation is prohibited. |
| **INACTIVE** | Configuration succeeded and resources are available, but normal operational activity is deliberately disabled. |
| **ACTIVE** | Normal operation is permitted. The subsystem may perform its defined work. |
| **ERROR** | The subsystem cannot safely continue normal operation and requires recovery or reconfiguration. |

**Implementation states** such as `IDLE`, `BUSY_TX`, `BUSY_RX`, `TX_PENDING`, `DMA_ARMED`, `MUX_PROBE`, and `BUS_OFF_RECOVERY` remain local to each component. They are not system lifecycle states.

## 2. Lifecycle Transitions

```text
UNCONFIGURED → INACTIVE (configure success)
UNCONFIGURED → ERROR (configure failure)
INACTIVE → ACTIVE (activate success)
INACTIVE → ERROR (activate failure)
ACTIVE → INACTIVE (deactivate)
ACTIVE → ERROR (fatal fault)
INACTIVE → UNCONFIGURED (cleanup)
ERROR → INACTIVE (recovery)
ERROR → ERROR (recovery fails, retry)
ANY → UNCONFIGURED (shutdown)
```

**Transition model:** For every transition, the service performs the interface-specific action first and then commits the result through the lifecycle core:

1. **Preconditions:** current state and dependencies are valid.
2. **Actions:** allocate/configure/start/stop/release interface-specific resources.
3. **Outputs/events:** update the lifecycle record and diagnostics.
4. **Result:** success reaches the defined target state; failure reaches `ERROR` (an invalid transition leaves state unchanged).

**Recovery semantics:** `recover` always ends in `INACTIVE`; explicit activation is required afterward. `shutdown` is a safety operation, not a normal fifth state. It stops activity, preserves diagnostics, and leaves the subsystem quiescent/unconfigured.

## 3. Fault Convention

**Firmware response levels:**

- **INFORMATIONAL:** Report an event; no output inhibit is required.
- **DEGRADED:** Preserve bounded operation with explicit validity/quality reporting; the owning service retains recovery responsibility.
- **FAULT:** Inhibit the affected normal output or operation and escalate through lifecycle recovery.
- **SAFETY_CRITICAL:** Immediately inhibit motion/outputs through the defined safety response and enter the required lifecycle fault path.

These are firmware response levels; no PL or SIL rating is claimed (PROJECT_CHARTER.md).

**Fault classes:**

- **Transient:** Expected to recover locally (e.g., one timeout). Retry within the service budget; reset the consecutive-failure count after success.
- **Persistent:** Repeated or sustained failure. Escalate the owning service to lifecycle `ERROR` or degrade the affected channel.
- **Fatal:** Unsafe system condition requiring motor inhibition, safe shutdown, or a controlled halt.
- **Configuration:** Invalid parameters or unavailable dependencies. Do not activate the dependent service.

**Fault diagnostics:** Every fault record should identify subsystem, operation, code, timestamp, occurrence count, and lifecycle state. Fault timestamps use the shared 64-bit monotonic time extension (from TIM2). A timestamp is marked synchronized only while the Pi-side ClockSync model is valid (PRM-TS-03 since the last accepted observation); the STM32 performs no clock math (TIME_SYSTEM_INTERFACE.md). Otherwise the record carries an unsynchronized quality indication.

## 4. Escalation Policy

Initial policy:

1. Classify the returned status (transient/persistent/fatal/configuration).
2. Perform the service-local retry budget within the service contract; reset the consecutive-failure count after success.
3. Enter `ERROR` after persistent threshold or any unsafe condition.
4. Recover to `INACTIVE` after verified recovery; require explicit activation afterward.

**Thresholds and retry delays remain per-service contract decisions** and must not be invented globally.

## 5. Safety Gates During Desynchronization

After ClockSync validity expires (PRM-TS-03 without an accepted observation):

- Acquisition and diagnostics continue.
- Timestamp quality reports `UNSYNCHRONIZED`.
- **Time-dependent motion is inhibited** until ClockSync validity is restored.
- Only explicitly defined non-motion service operations may continue.

Separately, Pi link loss (`link_stale`, SYS-FAIL-001) fails the STM32 motion gate closed. Single gated commands are not time-dependent motion; the gate inputs are in SYS-GATE-001 (ARCHITECTURE_DECISIONS.md, 2026-10-03).

Reset and recovery leave services `INACTIVE`; motion requires explicit reactivation after prerequisites pass.

## 6. Subsystem Mapping

| Subsystem | Classification | Lifecycle Responsibility |
| --- | --- | --- |
| Application/System Manager | Lifecycle-managed coordinator | Orders configuration, activation, shutdown, and dependency checks. |
| I2C Manager | Lifecycle-dependent subsystem | Owns I2C resource readiness; internal HAL transfer states remain local. |
| CAN Service | Lifecycle-managed subsystem | Owns CAN filter/start state, MKS transport availability, and motor-command gating. |
| SPI Slave Service | Lifecycle-managed subsystem | Owns host-transfer readiness and publication enablement. |
| Sensor Task/Service | Lifecycle-dependent subsystem | Requires I2C and mux readiness; sensor bring-up stages remain local. |
| Motor Service | Lifecycle-dependent subsystem | Future logical service; requires CAN `ACTIVE`. No separate implementation exists yet. |
| Health Monitor | Supporting service | Observes lifecycle and fault state; does not create readiness. |
| CubeMX/HAL setup | Hardware abstraction | Establishes hardware prerequisites before application lifecycle configuration. |

## 7. Dependency Rules

**Dependency graph:**

```text
HAL/CubeMX → I2C, CAN, SPI Slave services
I2C → Sensor;  CAN → Motor
Sensor, CAN, SPI → System Manager;  Health Monitor observes all
```

**Dependency constraints:**

- Sensor `ACTIVE` requires I2C and the TCA9548A path to be available.
- Motor `ACTIVE` requires CAN `ACTIVE`.
- Time-dependent motion requires valid time synchronization. Its expiry inhibits that motion while acquisition, diagnostics, and explicitly defined non-motion service operations continue.
- **Motion gate:** Individual service `ACTIVE` state does not by itself grant normal motor motion. The motion gate (SYS-GATE-001) must also be satisfied before normal motor motion is permitted.
- SPI may be `INACTIVE` while acquisition continues, but host publication must be unavailable or marked stale.
- Health Monitor may observe every state, including `ERROR` and shutdown diagnostics.
- A dependency in `UNCONFIGURED` or `ERROR` prevents dependent activation.
- A dependency in `INACTIVE` permits dependent configuration but not dependent activation.

## 8. Startup and Shutdown

**Startup sequence:**

1. CubeMX hardware initialization (clock, GPIO, DMA, peripherals, timer).
2. `osKernelInitialize` (RTOS kernel setup).
3. `App_Init()` (application configuration boundary; services configured to `INACTIVE`).
4. Task creation (establishes execution context; not itself activation).
5. `osKernelStart()` (scheduler begins).
6. System/application task performs dependency-ordered activation (I2C → CAN → SPI → Sensor → Motor → application).
7. Normal motor motion remains inhibited until the motion gate (SYS-GATE-001) is satisfied and explicit activation has been accepted.

**Shutdown order** (reverse of safety order): inhibit motor commands; stop sensor acquisition; stop SPI publication; stop normal CAN transmission; preserve diagnostics; leave peripherals safe.

**Timing rules:**

- CubeMX hardware initialization runs before `osKernelInitialize`; static RTOS object creation and lifecycle configuration run after it and before task creation.
- Activation, deactivation, cleanup, recovery, and shutdown run in task/system context only; no transition does heavyweight work from an ISR, and ISR callbacks defer state changes to service processing.
- Lifecycle checks are bounded state queries and preserve existing service timing.
- Lifecycle diagnostics and transition timestamps use the shared 64-bit monotonic time extension derived from TIM2.

## 9. Output Safety

While subsystems are not `ACTIVE` or during shutdown:

- **CAN not `ACTIVE`:** Inhibit normal motor commands.
- **Sensor not `ACTIVE`:** Publish records as invalid/stale.
- **SPI not `ACTIVE`:** DATA_READY low and no normal publication.
- **Any motor safety fault:** Inhibit motion and preserve emergency-stop policy.
- **Motion gate (SYS-GATE-001) false:** Inhibit normal motor motion even when individual services are otherwise `ACTIVE`.

## 10. Ownership and Reporting

- The final normal-motion decision is a system-level coordination function above individual service lifecycle ownership. The gate is implemented in `motion_permission.c`; its input set is SYS-GATE-001.
- The service that detects a fault owns local retry and recovery; the lifecycle owner decides state transition.
- HealthMonitor aggregates and reports; it must not silently recover a service unless a future contract explicitly grants that authority.
- ISR callbacks set minimal pending flags/counters and defer classification, lifecycle mutation, and recovery to task context.
- Diagnostics are available internally first, then through SPI `DIAGNOSTIC`/`EVENT` messages when transport is operational. A fault must not be cleared merely because it is no longer visible; recovery and clear semantics must be explicit.

## 11. Implementation Pattern

The reusable lifecycle implementation is intentionally small and static:

- States, transitions, results, and lifecycle records are defined. Each service owns its record; the lifecycle core owns no HAL handles, queues, buffers, or callbacks.
- Hardware actions occur in the service, which calls the lifecycle core with the action result. Mutation is synchronous and task/system-context only; ISR code may signal an event.
- No heap allocation, dynamic registration, event bus, inheritance, reflection, or external framework dependency is required.

## 12. Service Contracts

Each lifecycle-managed subsystem documents its identity, dependencies, state mapping, timing, buffer ownership, safety behavior when inactive/error/shutdown, and open decisions in its component contract under `Arm_Sensor_Hub/Documentation/`.

## Provenance

Reconciled from the former LIFECYCLE_CONTRACT.md and ERROR_HANDLING_STRATEGY.md (git history).
