# System Lifecycle

**Purpose:** Define the lifecycle vocabulary and state machine that controls subsystem readiness, safety gating, and recovery across the Karetao system.

The Karetao system uses a canonical four-state lifecycle inspired by ROS 2 Managed Nodes but implemented as a simple state machine in the STM32 firmware. Lifecycle state controls readiness and safety; it does not replace peripheral state machines or implementation-specific internal states.

---

## 1. Canonical States

| State | Meaning |
| --- | --- |
| **UNCONFIGURED** | Required configuration or resources are not ready. Normal operation is prohibited. |
| **INACTIVE** | Configuration succeeded and resources are available, but normal operational activity is deliberately disabled. |
| **ACTIVE** | Normal operation is permitted. The subsystem may perform its defined work. |
| **ERROR** | The subsystem cannot safely continue normal operation and requires recovery or reconfiguration. |

**Implementation states** such as `IDLE`, `BUSY_TX`, `BUSY_RX`, `TX_PENDING`, `DMA_ARMED`, `MUX_PROBE`, and `BUS_OFF_RECOVERY` remain local to each component. They are not system lifecycle states.

---

## 2. Lifecycle Transitions

The system supports the following transitions:

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
4. **Success:** transition reaches its defined target state.
5. **Failure:** transition reaches `ERROR` (except invalid transition, which leaves state unchanged).

**Recovery semantics:** `recover` always ends in `INACTIVE`; explicit activation is required afterward. `shutdown` is a safety operation, not a normal fifth state. It stops activity, preserves diagnostics, and leaves the subsystem quiescent/unconfigured.

---

## 3. Fault Convention

**Firmware response levels** (not a PL/SIL mapping or formal machine safety rating):

- **INFORMATIONAL:** Report an event; no output inhibit is required.
- **DEGRADED:** Preserve bounded operation with explicit validity/quality reporting; the owning service retains recovery responsibility.
- **FAULT:** Inhibit the affected normal output or operation and escalate through lifecycle recovery.
- **SAFETY_CRITICAL:** Immediately inhibit motion/outputs through the defined safety response and enter the required lifecycle fault path.

**These are firmware response levels, not a PL/SIL mapping or a formal machine safety rating.** The machine risk assessment and independent safety validation determine formal PL/SIL requirements.

**Fault classes:**

- **Transient:** Expected to recover locally (e.g., one timeout or temporary busy result). Retry within the service budget; reset consecutive-failure count after success.
- **Persistent:** Repeated or sustained failure that makes normal operation unreliable. Escalate the owning service to lifecycle `ERROR` or degrade the affected channel.
- **Fatal:** Unsafe system condition requiring motor inhibition, safe shutdown, or a controlled halt.
- **Configuration:** Invalid parameters or unavailable dependencies. Do not activate the dependent service.

**Fault diagnostics:** Every fault record should identify subsystem, operation, code, timestamp, occurrence count, and lifecycle state. Fault timestamps use the shared 64-bit monotonic time extension (from TIM2). A Pi-synchronized timestamp is valid only when the last accepted TIME_SYNC update is no older than five seconds; otherwise the record carries an unsynchronized quality indication.

---

## 4. Escalation Policy

Initial policy:

1. Classify the returned status (transient/persistent/fatal/configuration).
2. Perform the service-local retry budget within the service contract.
3. Reset consecutive-failure count after success.
4. Enter `ERROR` after persistent threshold or any unsafe condition.
5. Recover to `INACTIVE` after verified recovery.
6. Require explicit activation afterward.

**Thresholds and retry delays remain per-service contract decisions** and must not be invented globally.

---

## 5. Safety Gates During Desynchronization

After TIME_SYNC validity expires (5 seconds without an accepted update):

- Acquisition and diagnostics continue.
- Timestamp quality reports `UNSYNCHRONIZED`.
- **Time-dependent motion is inhibited** until a new accepted TIME_SYNC restores validity.
- Only explicitly defined non-motion service operations may continue.

Reset and recovery leave services `INACTIVE`; motion requires explicit reactivation after prerequisites pass.

---

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

---

## 7. Dependency Rules

**Dependency graph:**

```text
HAL/CubeMX initialized → I2C Service
                      → CAN Service
                      → SPI Slave Service
I2C → Sensor Service
CAN → Motor Service
Sensor → System Manager
CAN → System Manager
SPI → System Manager
Health Monitor ← (observes all)
```

**Dependency constraints:**

- Sensor `ACTIVE` requires I2C and the TCA9548A path to be available.
- Motor `ACTIVE` requires CAN `ACTIVE`.
- Time-dependent motion requires valid time synchronization. Its expiry inhibits that motion while acquisition, diagnostics, and explicitly defined non-motion service operations continue.
- **Proposed system motion permission:** Individual service `ACTIVE` state does not by itself grant normal motor motion. The proposed aggregate gate must also be satisfied before normal motor motion is permitted.
- SPI may be `INACTIVE` while acquisition continues, but host publication must be unavailable or marked stale.
- Health Monitor may observe every state, including `ERROR` and shutdown diagnostics.
- A dependency in `UNCONFIGURED` or `ERROR` prevents dependent activation.
- A dependency in `INACTIVE` permits dependent configuration but not dependent activation.

---

## 8. Startup and Shutdown

**Startup sequence:**

1. CubeMX hardware initialization (clock, GPIO, DMA, peripherals, timer).
2. `osKernelInitialize` (RTOS kernel setup).
3. `App_Init()` (application configuration boundary; services configured to `INACTIVE`).
4. Task creation (establishes execution context; not itself activation).
5. `osKernelStart()` (scheduler begins).
6. System/application task performs dependency-ordered activation (I2C → CAN → SPI → Sensor → Motor → application).

**Shutdown order** (reverse of safety order):
1. Inhibit motor commands.
2. Stop sensor acquisition.
3. Stop SPI publication.
4. Stop normal CAN transmission.
5. Preserve diagnostics.
6. Leave peripherals safe.

**Timing rules:**

- CubeMX hardware initialization runs before `osKernelInitialize`.
- Static RTOS object creation and application lifecycle configuration run after `osKernelInitialize` and before task creation.
- Activation, deactivation, cleanup, recovery, and shutdown run in task/system context only.
- No lifecycle transition performs heavyweight work from an ISR.
- ISR callbacks remain minimal and defer state changes to service processing.
- Active operation must preserve existing service timing; lifecycle checks are bounded state queries.
- All lifecycle diagnostics and transition timestamps use the shared 64-bit monotonic time extension derived from TIM2.

---

## 9. Output Safety

While subsystems are not `ACTIVE` or during shutdown:

- **CAN not `ACTIVE`:** Inhibit normal motor commands.
- **Sensor not `ACTIVE`:** Publish records as invalid/stale.
- **SPI not `ACTIVE`:** DATA_READY low and no normal publication.
- **Any motor safety fault:** Inhibit motion and preserve emergency-stop policy.

---

## 10. Ownership and Reporting

- The service that detects a fault owns local retry and recovery.
- The lifecycle owner decides state transition.
- HealthMonitor aggregates and reports; it must not silently recover a service unless a future contract explicitly grants that authority.
- ISR callbacks set minimal pending flags/counters and defer classification, lifecycle mutation, and recovery to task context.

**Diagnostics should be available:**
- Internally first.
- Through SPI `DIAGNOSTIC`/`EVENT` messages when transport is operational.
- A fault must not be cleared merely because it is no longer visible; recovery and clear semantics must be explicit.

---

## 11. Implementation Pattern

The reusable lifecycle implementation is intentionally small and static:

- States, transitions, results, and lifecycle records are defined.
- Each service owns its record; the lifecycle core does not own HAL handles, queues, buffers, or callbacks.
- Hardware actions occur in the service. The service calls the lifecycle core with the action result.
- Lifecycle mutation is synchronous and task/system-context only. ISR code may signal an event; deferred service code performs the transition.
- No heap allocation, dynamic registration, event bus, inheritance, reflection, or ROS 2 dependency is required.

---

## 12. Service Contracts

Every lifecycle-managed subsystem should document:

1. Identity, purpose, responsibilities, non-responsibilities
2. Dependencies and required lifecycle states of other subsystems
3. Canonical state mapping and supported transitions
4. Configuration, activation, active-state, deactivation, cleanup, shutdown, error, and recovery behavior
5. Input and output contracts
6. Timing requirements and budgets
7. Buffer ownership and concurrency rules
8. Safety behavior (outputs when inactive, error, or shutdown)
9. Resource ownership and diagnostics
10. Open architectural decisions

---

## Provenance

Reconciled from `docs/project/firmware/LIFECYCLE_CONTRACT.md` (lifecycle vocabulary, state machine, transitions, subsystem mapping, dependency rules, startup/shutdown sequence) and `docs/project/firmware/ERROR_HANDLING_STRATEGY.md` (fault convention, escalation policy, safety gates, output safety rules). All caveats preserved verbatim: "not a PL/SIL mapping", "firmware response levels", "thresholds remain per-service decisions", "explicit fault clear semantics", "independent safety validation required".
