⚠ **ARCHIVED — Non-normative historical document**

- **Archived:** 2026-09-20
- **Historical status:** Superseded proposal or earlier version
- **Superseded by:** Current system documentation in `Documentation/` framework

---

Phase 2 Integration Plan

Consolidated Recommendations, Proposed Decisions and Review Record

Status: Draft for final architectural review
Purpose: Consolidate the original TODO inventory, the first architectural assessment, and the second-agent review into a proposed Phase 2 execution baseline.

---

1. Executive Summary

The project has moved from an architecture-definition phase into an integration and evidence phase.

The principal architectural contracts are substantially established. Several individual services and protocol primitives are implemented and host-tested. However, the target system is not yet demonstrated as an integrated, deterministic, observable system on hardware.

The current Contract Status Matrix identifies the major remaining gates as:

- CAN physical/controller integration;
- maximum SPI clock and DMA hardware validation;
- exact MotorService/controller semantics;
- independent safety validation;
- target firmware build evidence.

The recommended Phase 2 strategy is therefore:

«Build a reliable integration spine first, expose subsystem diagnostics through it, then commission sensors and CAN against that observable system, followed by configuration persistence and MotorService.»

The agreed critical path is:

Target Build
    ↓
System Manager / RTOS / Lifecycle
    ↓
SPI Host + STM32 SPI DMA/NSS
    ↓
Snapshot + Time + Diagnostics
    ↓
Six-Sensor Integration
    ↓
CAN / MKS Commissioning
    ↓
Calibration + Mapping Persistence
    ↓
MotorService
    ↓
Integrated Motion

Safety validation runs independently and in parallel.

---

2. Architectural Principles

The following principles are proposed as Phase 2 non-negotiable rules.

2.1 Integration before abstraction

Do not add higher-level application abstractions merely because lower-level contracts exist.

MotorService remains gated on actual MKS controller commissioning.

2.2 SPI is the primary integration spine

SPI should lead CAN hardware commissioning because it provides the host-visible path for:

- sensor observations;
- motor feedback;
- lifecycle state;
- CAN diagnostics;
- snapshot statistics;
- time synchronization status;
- transport diagnostics.

The SPI transaction, buffer ownership and DATA_READY semantics are already defined in the existing contracts.

CAN wiring, tool preparation and software preparation may proceed in parallel, but actual controller commissioning should wait until the SPI diagnostic path is sufficiently operational to observe CAN behavior.

2.3 Lifecycle and readiness are distinct

The canonical lifecycle remains:

UNCONFIGURED
INACTIVE
ACTIVE
ERROR

System readiness is a separate derived condition.

"ACTIVE" therefore does not imply "READY_FOR_MOTION".

This preserves the existing lifecycle model and avoids adding readiness semantics to the lifecycle state machine itself.

2.4 Services own local recovery

The service that detects a fault owns service-local retry/recovery.

The SystemManager owns cross-service orchestration.

HealthMonitor observes and aggregates; it does not silently recover another subsystem.

This follows the existing error-handling and lifecycle contracts.

2.5 Evidence is part of implementation

A feature is not considered complete merely because its source code compiles.

Completion requires appropriate:

- automated test evidence;
- target build evidence;
- hardware measurements where applicable;
- retained configuration;
- contract/status update.

---

3. Proposed System Readiness Model

Introduce a static, derived "SystemReadiness" representation separate from lifecycle state.

Conceptually:

Configuration valid
        +
Calibration valid
        +
Joint mapping valid
        +
Sensor prerequisites satisfied
        +
CAN prerequisites satisfied
        +
SPI prerequisites satisfied
        +
Time synchronization valid
        +
Safety prerequisites satisfied
        ↓
READY_FOR_MOTION

A bitmask is recommended so that the exact failed prerequisite remains observable.

Example conceptual fields:

CONFIG_VALID
CALIBRATION_VALID
MAPPING_VALID
SENSORS_READY
CAN_READY
SPI_READY
TIME_SYNC_VALID
SAFETY_READY

The readiness state must be derived from current service/configuration state rather than becoming another independently mutable state variable.

Motion commands shall be rejected unless the required readiness conditions are satisfied.

This is a system capability decision, not a replacement for the lifecycle contract.

---

4. Proposed SystemManager

Introduce a SystemManager/Application Manager responsible for system-level sequencing.

Responsibilities

- dependency-ordered configuration;
- service activation;
- readiness calculation;
- recovery orchestration;
- shutdown sequencing;
- explicit post-recovery reactivation;
- global motion-readiness gating.

Non-responsibilities

The SystemManager must not own:

- CAN queues;
- SPI frame buffers;
- I2C transfers;
- sensor algorithms;
- MKS protocol encoding;
- local service retry logic.

The lifecycle contract already establishes this separation of concerns.

---

5. RTOS and IPC Architecture

The current planning context explicitly identifies task topology and IPC as incomplete.

Before substantial integration code is added, document the final task architecture.

At minimum define:

Component| Responsibility
SystemManager| lifecycle, readiness, cross-service recovery
SensorTask| six-channel acquisition
CAN service/task context| CAN processing and scheduling
SPI service/task context| request processing, frame staging, DMA completion
HealthMonitor| aggregation/reporting
Watchdog supervision| system/task-progress supervision

The exact number of RTOS tasks may be minimized where safe; the important requirement is clear ownership and bounded execution.

For each execution context define:

- priority;
- period or trigger;
- worst-case execution time;
- stack allocation;
- queues/notifications;
- blocking rules;
- ISR relationship.

---

6. Watchdog Architecture

Add watchdog implementation as an explicit Phase 2 foundation task.

Proposed ownership

Use a dedicated watchdog supervisory mechanism.

The proposed structure is:

Child tasks
   ↓
progress/heartbeat
   ↓
SystemManager
   ↓
system heartbeat
   ↓
Watchdog supervisor

The watchdog should not simply check that the CPU is alive.

It should verify that required application execution paths are making progress.

The exact watchdog peripheral, timeout, boot-loop handling and fault-report mechanism remain implementation decisions unless separately frozen.

---

7. Golden Baseline and Rollback

Introduce an explicit golden-baseline procedure before invasive SPI DMA or CAN physical integration changes.

The recommended baseline should contain:

Golden firmware image
Golden ELF/map metadata
Build metadata
Known-good configuration
Known-good hardware revision
Baseline test result
SHA-256 checksum

A binary flash backup should be retained using the project's supported ST-LINK/ST flashing workflow.

The rollback acceptance criterion should be:

Restore golden image
        ↓
Power cycle
        ↓
Run baseline smoke test
        ↓
SPI responds correctly

The initial proposed smoke-test condition is:

«PING request receives the expected valid response within 100 ms.»

However, "entire flash region" should not become the permanent requirement until the actual STM32 memory map, bootloader ownership, option bytes and programmer procedure are explicitly established.

The golden image must be restorable without accidentally overwriting protected or independently managed regions.

---

8. P0 SPI Integration

8.1 Raspberry Pi Driver

Complete:

- fixed 512-byte transfer;
- protocol-version rejection;
- schema-version validation;
- CRC validation;
- sequence tracking;
- stale/duplicate rejection;
- retry policy;
- timeout policy;
- transport diagnostics.

The current review has identified a concrete mismatch: the host decoder still accepts arbitrary "protocol_version" values even though the contract requires unsupported versions to be rejected.

This should be resolved before hardware acceptance.

8.2 Linux Backend

Freeze:

- SPI device path;
- SPI mode 0;
- initial 5 MHz maximum;
- transfer length;
- GPIO access mechanism;
- DATA_READY polarity;
- polling/edge strategy.

Placeholder device paths and unimplemented backend methods should be removed.

8.3 STM32 DMA/NSS

Implement and verify the hardware state machine around:

IDLE
 ↓
ARMED
 ↓
NSS asserted
 ↓
DMA active
 ↓
NSS released
 ↓
DMA complete
 ↓
request processing
 ↓
response staging
 ↓
ARMED

Explicit abort/error paths must cover:

- NSS abort;
- DMA error;
- incomplete transaction;
- malformed request;
- repeated transport failure.

The SPI service contract requires that partial transactions never expose partial application state and that ownership is safely re-established.

---

9. Snapshot Integration

Implement the canonical snapshot serializer after the SPI transport is operational enough to consume it.

The target v1 six-sensor/eight-motor payload is:

12-byte snapshot prefix
+ 6 × 24-byte sensor records
+ 8 × 24-byte motor records
= 348-byte payload

18-byte header
+ 348-byte payload
+ 4-byte CRC
= 370-byte frame

within the 512-byte maximum.

Serialization must:

- use explicit field offsets;
- use explicit little-endian encoding;
- preserve fixed record counts;
- preserve invalid/stale records;
- include record timestamps;
- calculate CRC over the approved coverage;
- reject oversize payloads.

No C-structure layout is to be treated as a wire-format definition.

---

10. Time Synchronization

The existing v1 time model remains the baseline:

hub_time_us = local_time_us + signed_offset_us

with:

- Pi as authority;
- STM32 monotonic local time;
- extended 64-bit time;
- five-second validity;
- sequence validation;
- direct offset steps.

Remaining implementation/validation work:

- migrate remaining raw TIM2 timestamps;
- validate wrap extension;
- validate accepted and rejected TIME_SYNC;
- validate duplicate/stale sequence handling;
- validate five-second expiry;
- validate resynchronization;
- validate motion inhibition when time synchronization is invalid.

---

11. P0 Sensor Integration

Implement the full six-channel acquisition path.

Target:

Logical axis 0 → TCA9548A channel 0 → AS5600
Logical axis 1 → TCA9548A channel 1 → AS5600
Logical axis 2 → TCA9548A channel 2 → AS5600
Logical axis 3 → TCA9548A channel 3 → AS5600
Logical axis 4 → TCA9548A channel 4 → AS5600
Logical axis 5 → TCA9548A channel 5 → AS5600

Before freezing the implementation, define:

- scan period;
- mux settle time;
- per-channel timeout;
- retry count;
- cool-down;
- maximum complete-scan time;
- minimum healthy-channel threshold.

A failed channel should not automatically prevent healthy channels from being sampled.

Every snapshot should retain six stable sensor records, including invalid/stale records where necessary.

---

12. P0 CAN Commissioning

CAN software preparation and physical setup may proceed while SPI is being completed.

Actual MKS controller commissioning begins after the SPI diagnostic path is usable.

Required evidence

Identify and record:

- exact controller model;
- firmware revision;
- transceiver;
- wiring;
- termination;
- topology;
- cable length;
- stub lengths;
- node count;
- bitrate;
- sample point;
- command IDs;
- response IDs;
- response DLC;
- response timing;
- polling behavior.

The currently applied 1 Mbps timing remains an engineering calculation rather than validated hardware evidence:

42 MHz APB1
Prescaler = 3
BS1 = 11
BS2 = 2
SJW = 1

1 Mbps
85.7 % sample point

---

13. CAN Bus-Off Semantics

The current implementation has a significant policy issue requiring explicit resolution.

Following a bus-off event, the service can become:

Lifecycle = ACTIVE
Normal commands = inhibited

without a direct path back to normal commands until a later escalation/recovery sequence.

The CAN developer guide identifies this as a real gap.

The proposed decision is:

«A bus-off recovery shall return CAN to "INACTIVE", not "ACTIVE".»

Normal operation shall require an explicit subsequent "CanService_Activate()" request.

This provides a clear operational acknowledgement boundary following recovery and avoids an apparently active service silently resuming motion-related traffic.

This should be reflected consistently in:

- CAN service;
- lifecycle contract;
- readiness logic;
- diagnostics;
- host behavior.

---

14. CAN Software Policy

The existing bounded CAN mechanisms should be retained unless hardware evidence demonstrates the need for change.

These include:

- priority ordering;
- bounded TX queue;
- bounded retries;
- response timeout tracking;
- duplicate CAN-ID rejection;
- HAL error diagnostics;
- FIFO overflow diagnostics;
- bus-off recovery.

The current CAN implementation already contains substantial policy and should not be rewritten merely to fit the new backlog structure.

Instead, the focus should be validation against the physical controller.

---

15. Payload Schema Freeze

The recommendation is to freeze v1 as a fixed wire format.

For v1:

- fixed record sizes;
- fixed field offsets;
- fixed-width counters;
- explicit schema versions;
- no tagged extension mechanism.

Tagged extensions and more elaborate forward-compatibility mechanisms should be explicitly deferred to v1.1.

This avoids introducing unnecessary parser and interoperability complexity during the initial integration cycle.

The current payload document should be reconciled with the freeze document so that speculative future decisions do not continue to appear as v1 blockers.

---

16. Diagnostic Counter Semantics

A v1 fixed-width diagnostic counter is preferable.

The proposed width is:

uint32_t

However, one point requires wording correction before freezing:

«"Counters saturate at UINT32_MAX and wrap to 0."»

These are two different behaviors.

The architecture must select one:

Option A — Wrap

UINT32_MAX → 0

Option B — Saturate

UINT32_MAX → UINT32_MAX

For monotonically accumulating diagnostic counters, wrapping is reasonable provided the host protocol documents modulo-32-bit behavior and the host does not interpret a wrapped value as a negative event.

This point should be explicitly resolved before the schema is frozen.

---

17. HealthMonitor

HealthMonitor should aggregate and report, but not silently recover services.

Required work:

- health thresholds;
- severity classification;
- subsystem aggregation;
- host reporting;
- EVENT/DIAGNOSTIC generation;
- acknowledgement/clear semantics.

The error strategy already defines the desired authority boundary.

---

18. Calibration and Mapping

Calibration persistence should be completed before serious motor integration.

Recommended flow:

Persisted calibration
        +
Persisted mapping
        ↓
Validation
        ↓
Cross-version compatibility
        ↓
System readiness
        ↓
MotorService activation

The calibration contract explicitly leaves flash storage, write ordering, power-loss recovery and endurance work outstanding.

The joint mapping contract requires one-to-one v1 mapping and explicitly excludes coupled/differential topology from the current schema.

Do not introduce coupled/differential extensions until required by the physical mechanism and intentionally versioned.

---

19. MotorService Gate

MotorService remains a gated activity.

No substantial MotorService implementation should proceed until the exact MKS controller behavior has been commissioned.

Required inputs include:

- exact command semantics;
- response format;
- timing;
- state behavior;
- enable/disable behavior;
- stop behavior;
- feedback semantics;
- fault behavior.

The MotorService contract intentionally leaves these semantics open until controller commissioning.

This should remain a hard dependency.

---

20. Safety Workstream

Safety validation remains an independent parallel workstream.

Firmware contributes:

- lifecycle gating;
- readiness gating;
- watchdog behavior;
- fault reporting;
- deterministic reset/recovery.

External/system safety work owns:

- independent E-stop;
- power removal;
- safety-rated control architecture;
- stopping/braking validation;
- risk assessment;
- PL/SIL determination.

The safety checklist explicitly states that firmware tests/builds are not substitutes for hardware evidence or external safety assessment.

No firmware readiness flag should be interpreted as establishing a formal PL/SIL rating.

---

21. Human + Code Agent Execution Model

Phase 2 should be operated as a closed Human + Code Agent validation loop.

Code Agent responsibilities

- implementation;
- unit tests;
- host tests;
- build automation;
- protocol validation;
- log analysis;
- timing/load calculations;
- evidence templates;
- contract/status maintenance after approved decisions.

Human responsibilities

- hardware setup;
- flashing;
- wiring;
- oscilloscope/logic-analyzer measurement;
- CANable operation;
- controller identification;
- safety measurements;
- physical acceptance decisions.

Execution loop

Code
 ↓
Automated validation
 ↓
Human hardware test
 ↓
Captured evidence
 ↓
Analysis
 ↓
Architectural decision
 ↓
Contract/status update
 ↓
Next integration step

Neither side should substitute assumptions for physical evidence.

---

22. Proposed Phase 2 Backlog

P0 — Foundation

- Restore embedded target build.
- Establish SystemManager.
- Freeze RTOS task/IPC topology.
- Establish System Readiness.
- Establish watchdog architecture.
- Establish golden baseline/rollback.
- Establish memory/resource budget.

P0 — SPI

- Complete Raspberry Pi driver.
- Complete Linux backend.
- Complete STM32 DMA/NSS integration.
- Implement snapshot serializer.
- Complete TIME_SYNC integration.
- Validate SPI at 5 MHz.
- Establish reliable host-visible diagnostics.

P0 — Sensors

- Complete six-channel scheduler.
- Freeze scan timing/failure policy.
- Commission all six channels.
- Complete timestamp migration.

P0 — CAN

- Establish physical topology.
- Commission MKS controller.
- Validate applied CAN timing.
- Characterize controller traffic.
- Validate polling/load.
- Validate bus-off recovery.
- Freeze post-recovery activation semantics.

P1 — Configuration

- Implement calibration persistence.
- Implement mapping persistence.
- Bind mapping/calibration versions.
- Integrate configuration with System Readiness.

P1 — System Integration

- Complete HealthMonitor.
- Complete diagnostics/events.
- Complete System Readiness integration.
- Perform sensor → CAN → SPI end-to-end testing.
- Perform long-duration soak testing.

P1 — MotorService

- Freeze controller-informed MotorService contract.
- Implement MotorService.
- Implement command timeout/completion/cancellation.
- Implement motor state/fault handling.

P0-Release — Safety

- Machine risk assessment.
- PL/SIL determination.
- Independent E-stop.
- Motor power-disable path.
- Watchdog validation.
- Actuator stop/brake validation.
- Stopping-time measurement.
- Safety architecture review.
- Final energized-motion release review.

---

23. Phase 2 Definition of Done

Phase 2 is complete when the following are demonstrated.

Build

- Debug target build passes.
- Release target build passes.
- Host tests pass.
- Memory/resource budget is recorded.
- Golden rollback image is retained.

Lifecycle / Readiness

- startup ordering follows the lifecycle contract;
- services reach "INACTIVE" before activation;
- SystemManager performs dependency-ordered activation;
- recovery ends in "INACTIVE";
- explicit reactivation is required;
- "READY_FOR_MOTION" remains distinct from lifecycle "ACTIVE".

SPI

- Pi driver validates protocol/schema/CRC;
- sequence tracking works;
- STM32 DMA/NSS is operational;
- 512-byte transfers are validated;
- DATA_READY behavior is measured;
- snapshot data reaches the Pi;
- host-stall and aborted transactions are safe;
- initial 5 MHz acceptance evidence is retained.

Sensors

- all six AS5600 channels operate;
- failed channels remain isolated from healthy channels;
- six stable sensor records are published;
- timestamp quality is correct.

CAN

- exact controller behavior is known;
- physical network is documented;
- bitrate is hardware validated;
- polling/load is measured;
- controller responses are characterized;
- bus-off/recovery is demonstrated;
- normal traffic requires explicit reactivation after recovery.

Configuration

- mapping is commissioned;
- calibration is validated;
- persistence is validated;
- configuration/readiness dependencies are enforced.

End-to-End

A deliberate fault test shall demonstrate:

«A physically disconnected CAN path produces the expected diagnostic/fault indication, which becomes observable through the Raspberry Pi over SPI, without modifying firmware between the fault injection and observation.»

This is intended to verify the entire diagnostic chain:

Physical fault
 ↓
CAN detection
 ↓
Service diagnostics/lifecycle
 ↓
Snapshot/diagnostic publication
 ↓
SPI
 ↓
Raspberry Pi

The exact message type used for this evidence should be selected according to the final v1 payload contract; it should not be assumed that every diagnostic must be embedded inside the normal "SNAPSHOT".

Safety

All applicable safety release blockers have independently reviewed evidence.

---

24. Proposed Evidence Structure

Use a consistent evidence tree:

Documentation/Evidence/
├── build/
├── spi/
├── sensors/
├── can/
├── time-sync/
├── calibration/
├── mapping/
├── system/
└── safety/

Each evidence record should identify:

Test ID
Hardware revision
Firmware revision
Configuration
Procedure
Instrumentation
Raw evidence
Measured result
Expected result
Pass/Fail
Reviewer
Date

This prevents hardware validation from becoming dependent on undocumented laboratory state.

---

25. Architectural Review Questions

The following questions should be answered before this document is adopted as the official Phase 2 baseline.

Q1 — SPI lead

Do you approve SPI as the integration spine and therefore require reliable SPI diagnostic publication before actual MKS controller commissioning?

Q2 — System Readiness

Do you approve a derived "SystemReadiness" bitmask independent of lifecycle state?

Q3 — SystemManager

Do you approve centralized cross-service orchestration through SystemManager while retaining local recovery ownership inside individual services?

Q4 — CAN recovery

Do you approve CAN bus-off recovery returning the service to "INACTIVE" and requiring explicit reactivation?

Q5 — Fixed SPI frames

Do you approve fixed 512-byte SPI transfers for v1 with no transport wrapper?

Q6 — v1 schema

Do you approve deferring tagged/extension mechanisms to v1.1?

Q7 — Counter semantics

Which counter behavior is required for v1?

WRAP:
UINT32_MAX → 0

or

SATURATE:
UINT32_MAX → UINT32_MAX

The current proposal must not describe both simultaneously.

Q8 — Watchdog

Do you approve the proposed supervisory structure:

Child task health
      ↓
SystemManager
      ↓
Watchdog supervisor

and what exact heartbeat/progress conditions must be satisfied?

Q9 — Memory margin

Do you approve:

- «25% free RAM;»
- «20% free Flash;»

as Phase 2 baseline targets?

Should these be measured against Debug, Release, or both?

Q10 — Golden image

Do you approve a binary backup plus SHA-256 as the rollback baseline, subject to explicit confirmation of the STM32 flash map and bootloader ownership?

Q11 — MotorService

Do you approve the hard gate that MotorService semantics cannot be frozen until exact MKS controller behavior has been physically commissioned?

Q12 — Safety boundary

Do you approve treating physical E-stop, power removal, stopping time and formal safety architecture as external/system safety responsibilities while firmware readiness gates only act as supplementary controls?

Q13 — End-to-end diagnostic test

Do you approve the CAN-disconnect test as a mandatory Phase 2 acceptance criterion?

If yes, should its required output be:

- a "DIAGNOSTIC" message;
- an "EVENT";
- a "SNAPSHOT" diagnostic flag;
- or any contract-approved host-visible representation?

Q14 — Evidence authority

Do you approve the hierarchy:

Approved contract
      ↓
Implementation
      ↓
Hardware evidence
      ↓
Release decision

with the following rule:

- code disagreement with the approved contract is an implementation defect;
- hardware disagreement with the contract means the architectural assumption must be reviewed rather than silently overriding the contract.

Q15 — Target build

Do you approve target-build availability as the first mandatory P0 gate before invasive integration work?

Q16 — Phase 2 scope

Are there any additional architectural gates that should prevent the project from entering MotorService/integrated-motion development after the stated Phase 2 Definition of Done is achieved?

---

26. Proposed Decision

Subject to the answers above, the recommended Phase 2 operating principle is:

«Move from document-driven development to evidence-driven integration.»

The team should not optimize for completing the TODO list.

It should optimize for proving, in order:

Build works
    ↓
Lifecycle works
    ↓
SPI works
    ↓
Diagnostics are observable
    ↓
Sensors work
    ↓
CAN works
    ↓
Time/configuration are valid
    ↓
Motor semantics are known
    ↓
System is ready
    ↓
Safety case is independently accepted
    ↓
Motion is released

This preserves the approved architectural foundations while minimizing integration rework and making each subsequent development step observable and reversible.
