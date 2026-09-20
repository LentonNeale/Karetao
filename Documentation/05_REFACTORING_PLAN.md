# Documentation Refactoring Plan — `docs/project/**` → `Documentation/**`

**Status:** Proposed. Not yet executed.
**Governs:** Migration of all remaining legacy content under `docs/project/**` into the Karetao documentation framework.
**Governed by:** [`01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md`](01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md) (authority), [`05_REFACTORING_RULES.md`](05_REFACTORING_RULES.md) (method), [`06_IMPLEMENTATION_CHECKLIST.md`](06_IMPLEMENTATION_CHECKLIST.md) (scope control).

This document is a governance/process artifact. It defines no system requirements and carries no authority over any system-level document.

---

## 1. Purpose

Steps 1–3 of the refactoring sequence (establish authority model, establish component model, approve framework) are complete. Steps 4–6 (inventory, classify, determine authority) are complete for the decision material only. This plan covers steps 7–12 for the remaining legacy content.

The objective from `05_REFACTORING_RULES.md` applies unchanged: **fewer competing sources of truth, with information and traceability retained.** Emptying `docs/` is the consequence, not the goal.

---

## 2. Current state

### 2.1 What has already been reconciled

| Legacy source | Destination | State |
|---|---|---|
| `SD/SD-01.md` … `SD/SD-26.md`, `SYSTEM_DECISIONS.md` | `01_SYSTEM/SYSTEM_REQUIREMENTS.md` (SYS-* table), `07_DECISIONS/KARETAO_..._REGISTER.md` §1 | Reconciled |
| `Open_Items_List.md` (145 questions) | `07_DECISIONS/KARETAO_..._REGISTER.md` §2 | Reconciled |
| `system/TODO_List.md`, `archive/.../CAN_Module_TODO.md`, `firmware/CONTRACT_STATUS.md` | `07_DECISIONS/KARETAO_..._REGISTER.md` §3 | Reconciled |
| `firmware/SAFETY_RELEASE_CHECKLIST.md` | `04_SAFETY/*` (SAFE-001…009), register §4 | Reconciled |
| `system/architecture.md` (system-level layer only) | `01_SYSTEM/SYSTEM_ARCHITECTURE.md` | Partially reconciled |

### 2.2 What has not

`Documentation/**` is ~2,190 lines, of which ~1,340 are the authority model, component model, and decision register. The eleven system/interface/safety/verification/configuration documents total ~330 lines and are **summary tables of SD outcomes**, not contracts.

`docs/project/**` is ~9,200 lines, of which ~5,900 are live technical content that has no representation in `Documentation/**` at any level of detail: wire framing tables, payload layouts, CRC parameters, state machines, timing budgets, pinouts, bring-up procedure.

The gap is concrete. `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` is 22 lines and states the frame is 512 bytes. `docs/project/protocols/spi-contract.md` is 306 lines and defines the 18-byte header field-by-field, the pipelined transaction model, sequence/correlation rules, the armed-then-assert `DATA_READY` model, and twelve contract invariants. **A reader today cannot implement or verify the SPI interface from `Documentation/**` alone.** The same holds for TIME, HOST, and CAN.

### 2.3 Scope direction

Per the direction given on this plan: **all system-level information and all cross-boundary contracts are to live in the Karetao repository.** Section 4 applies that direction. Section 4.4 lists the residual that the authority model places outside Karetao, and flags it for an explicit per-file decision rather than assuming it.

---

## 3. Classification method

Each legacy document is classified statement-by-statement, not file-by-file, per `05_REFACTORING_RULES.md` § Classification. The test applied throughout:

| Test | Owner | Destination |
|---|---|---|
| Does the statement constrain what crosses a boundary between two Karetao components, or between Karetao and the outside world? | Karetao | `01_SYSTEM/`, `02_INTERFACES/`, `04_SAFETY/`, `06_CONFIGURATION/` |
| Is the statement observable only inside one component (task structure, HAL calls, DMA mechanics, build flags, source filenames)? | Component | Component repository |
| Is the statement a measurement, test result, or claim about what has been run? | Verification | `05_VERIFICATION/` as evidence reference; never promoted to a requirement |
| Does the statement describe externally defined equipment or protocol behaviour (MKS, AS5600, TCA9548A, STM32F405)? | External | Referenced as external authority; never rewritten as a Karetao requirement |
| Is the statement a record of a past project state, superseded proposal, or conversation? | Historical | `99_ARCHIVE/` |

A `_CONTRACT.md` filename does not by itself make a document a Karetao system contract. `CAN_SERVICE_CONTRACT.md` is a contract between application code and `CanService`; that boundary is internal to the Arm Sensor Hub. `spi-contract.md` is a contract between the Pi and the STM32; that boundary is a Karetao system interface. Both are "contracts"; only the second is Karetao-owned.

---

## 4. Disposition

### 4.1 Karetao system authority — content that moves into `Documentation/**`

| Source | Lines | Destination | Action |
|---|---:|---|---|
| `protocols/spi-contract.md` | 306 | `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | **Expand the stub into the full contract.** Absorb §§1–18 except §9's buffer-ownership mechanics and §15's STM32-internal obligations. Header table, transaction model, message types, sequence/correlation, `DATA_READY` semantics, error handling, versioning rule and the 12 invariants are all system-visible. |
| `protocols/spi-payload-schema.md` | 164 | `02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md` (new) | **Move whole.** Wire payload layouts are by definition cross-boundary. Serializer/decoder implementation is not in this file. |
| `firmware/TIMESTAMP_SYNC_CONTRACT.md` | 59 | `02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`; `01_SYSTEM/SYSTEM_SYNCHRONIZATION.md` | **Split.** Time model (`hub_time_us = local_time_us + time_offset_us`, Pi as time authority, monotonicity rule, measurement-vs-frame timestamp distinction), TIME_SYNC transaction, validity and quality reporting → Karetao. TIM2/`TimeService_NowUs()` wrap handling, reader-context restriction, AS5600 timestamp migration → component (§4.4). |
| `firmware/SNAPSHOT_COHERENCY_CONTRACT.md` | 109 | `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md` | **Split.** Snapshot coherency guarantee, replace-if-new semantics, drop/replace diagnostics, six-record fixed shape → Karetao. Producer-cache/two-frame buffer ownership and DMA-immutability mechanics → component. |
| `firmware/JOINT_MAPPING_CONTRACT.md` | 28 | `01_SYSTEM/SYSTEM_REQUIREMENTS.md` (SYS-MAP-001 detail), `06_CONFIGURATION/SYSTEM_CONFIGURATION.md` | **Move whole.** Logical-joint ↔ sensor ↔ CAN-ID mapping is the system's identity model. Carry the explicit statement that schema v1 cannot represent the differential end effector — it is the concrete blocker behind SYS-MECH-001. |
| `firmware/CALIBRATION_CONTRACT.md` | 30 | `06_CONFIGURATION/SYSTEM_CONFIGURATION.md` | **Move whole.** Record model, versioning, CRC, redundancy and the Pi-computes/STM32-validates ownership split are the substance of SYS-CAL-001/002. |
| `firmware/LIFECYCLE_CONTRACT.md` | 240 | `01_SYSTEM/SYSTEM_LIFECYCLE.md` (new, in `01_SYSTEM/`) | **Move the vocabulary and state semantics.** The canonical state set and transition rules are referenced by CAN, SPI, HOST and safety gating; they are system-level. Per-service activation order and FreeRTOS task context → component. |
| `firmware/ERROR_HANDLING_STRATEGY.md` | 68 | `01_SYSTEM/SYSTEM_LIFECYCLE.md` or `04_SAFETY/SAFETY_INTEGRATION.md` | **Split.** The four response levels and the escalation-to-lifecycle rule are system semantics, and the explicit "these are not a PL/SIL mapping" caveat must survive verbatim. HealthMonitor internals → component. |
| `firmware/CONTRACT_V1_FREEZE.md` | 209 | `07_DECISIONS/` + `99_ARCHIVE/SUPERSEDED/` | **Harvest, then archive.** Its frozen v1.0 decisions must be checked against the SYS-* table and any not represented there recorded as decisions. Its contract hierarchy diagram is superseded by this framework. See conflict C-1. |
| `interfaces/raspberry-pi-spi.md` | 61 | `02_INTERFACES/SPI/` (hardware baseline); `05_VERIFICATION/` (validation reqs) | **Split.** Physical link baseline is the missing evidence behind SYS-SPI-004; its validation requirements are verification items. |
| `interfaces/spi-service-contract.md` | 135 | mostly component (§4.4) | **Split.** `DATA_READY` timing, host-stall timeout and error/NACK behaviour are host-observable → Karetao. Lifecycle-of-service, DMA arm/abort/re-arm, buffer ownership → component. |
| `firmware/CAN_SERVICE_CONTRACT.md` | 133 | `02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md` | **Split.** Bus-off inhibit/recovery/escalation behaviour, retry bounds and latest-value freshness semantics are system-observable. `CanService` API, queues and HAL handling → component. MKS command encoding remains external authority — reference, do not restate. |
| `firmware/MULTI_SENSOR_CONTRACT.md` | 79 | `03_COMPONENTS/ARM_SENSOR_HUB.md` (topology table only) | **Split.** The logical-axis ↔ mux-channel ↔ sensor table is the system's sensor identity map. TCA9548A/AS5600 register protocol is external authority; SensorTask scheduling is component. |
| `firmware/MOTOR_SERVICE_CONTRACT.md` | 49 | `99_ARCHIVE/SUPERSEDED/` + one decision entry | **Archive.** Self-declared "future design contract", not implemented. Its six-axis model and CAN-ID commissioning assumption are already covered by SYS-MAP-001. |
| `firmware/APP_OVERVIEW.md` | 8 | `01_SYSTEM/SYSTEM_OVERVIEW.md` | **Use as seed.** `SYSTEM_OVERVIEW.md` is currently a 3-line placeholder; this is the only plain-language statement of what the system does. Rewrite at system scope — the source is written from the STM32's point of view. |
| `system/architecture.md` | 110 | `01_SYSTEM/SYSTEM_ARCHITECTURE.md` | **Complete the partial reconciliation.** Startup flow and data flow are system-level and are not yet represented. "What Is Mature Vs What Is Emerging" → `05_VERIFICATION/INTEGRATION_GATES.md` as status, not requirement. "Files Interns Should Learn Early" → component. |
| `hardware/arm-sensor-hub-baseline.md` | 226 | `03_COMPONENTS/ARM_SENSOR_HUB.md`; remainder component | **Split.** System-visible: MCU family, clock tree as it constrains CAN/SPI timing, and the interface pin assignments other components depend on (SPI3, DATA_READY, CAN1, I2C1). Full pinout, peripheral notes and build config → component. |
| `firmware/CAN_BIT_TIMING_EVIDENCE.md` | 48 | `05_VERIFICATION/` as evidence reference | **Reference, do not promote.** Self-declared "engineering calculation; not hardware validation". It is the evidence trail for the SYS-CAN-001 1 Mbps target and records that the generated code currently runs 875 kbps. See conflict C-2. |

### 4.2 Historical — content that moves to `99_ARCHIVE/`

| Source | Destination |
|---|---|
| `archive/Arm_Sensor_Hub/Documentation/Conversations/*` (CTO_DECISION_BRIEF, CTO_DECISION_FINAL, DeepSeek, GPT, InterAgent_Chat — 1,200 lines) | `99_ARCHIVE/CONVERSATIONS/` |
| `archive/agent_messages/*`, `archive/Agent_messages/*` | `99_ARCHIVE/CONVERSATIONS/` |
| `archive/.../Sprint_1_List.md`, `Sprint Info/Sprint_2_Readiness_Report.md`, `PHASE_1_FINAL_CLEARANCE_REPORT.md` | `99_ARCHIVE/SPRINTS/` |
| `archive/docs/proposed_phase2.md` (1,064 lines) | `99_ARCHIVE/SUPERSEDED/` |
| `archive/docs/RASPBERRY_PI_BRINGUP_V0.md` | `99_ARCHIVE/SUPERSEDED/` — superseded by V0.1 |
| `archive/.../OnboardingDocs/First_Week_Guide.md`, `Project_Orientation.md`, `README.md` | `99_ARCHIVE/SUPERSEDED/` |
| `SD/SD-01.md` … `SD-26.md`, `SYSTEM_DECISIONS.md`, `Open_Items_List.md`, `system/TODO_List.md`, `firmware/CONTRACT_STATUS.md`, `firmware/SAFETY_RELEASE_CHECKLIST.md` | `99_ARCHIVE/DECISIONS/` — **only after** §6 confirms each is fully represented in the register |

`CTO_DECISION_FINAL.md` is the approved baseline for SD-01–SD-25. Archiving it is correct — the register records it as the approval evidence — but its archive entry must state that it is the origin of the approvals, not merely a conversation.

`06_IMPLEMENTATION_CHECKLIST.md` line 50 currently reads "Archived `docs/project/archive/**` content is excluded from current migration." That line must be amended, since this plan migrates it.

### 4.3 Deletion

Five files only, all of them deprecated 5-line pointer stubs whose links are already broken (they point at `/docs/protocols/...`, `/docs/architecture.md` and similar paths that no longer exist):

`archive/.../SPI_CONTRACT.md`, `archive/.../SPI_PAYLOAD_SCHEMA.md`, `archive/.../SPI_SERVICE_CONTRACT.md`, `archive/.../PROJECT_BASELINE.md`, `archive/.../OnboardingDocs/Architecture_and_Runtime_Flow.md`, `archive/RaspberryPi_Sensor_Hub/docs/spi.md`.

Per `05_REFACTORING_RULES.md` § Deletion, each must first be confirmed to carry no unique information beyond the pointer and to have no inbound links. They carry none; their purpose was to redirect to files that have since moved twice.

`archive/.../Arm_Sensor_Hub/Documentation/README.md` and `PROJECT_BASELINE.md` (5 lines) are in the same category.

### 4.4 Residual outside Karetao — requires your decision

The direction is that all system information and contracts live in Karetao. Applying §4.1 achieves that. What remains after the splits is content that is observable only inside one component, and that `DOCUMENTATION_AUTHORITY_MODEL.md` § "Arm Sensor Hub component authority" assigns to the component repository:

| Content | Volume | Nature |
|---|---:|---|
| `firmware/BUILD_CONTRACT.md` | 73 | C11/C++17 split, CMake presets, toolchain, `HostTests` target |
| `firmware/I2C_MANAGER_CONTRACT.md` | 69 | I2C1 transfer serialization, HAL status mapping |
| `firmware/HEALTH_MONITOR_CONTRACT.md` | 51 | `HealthMonitor` internals; self-declared "design target" |
| `operations/RASPBERRY_PI_BRINGUP_V0.1.md` | 1,757 | Pi 5 provisioning: imager, cloud-init, PREEMPT_RT, ROS 2 Jazzy install, governor, SPI enable |
| `system/development.md` | 115 | Local build/test commands for both subtrees |
| Split remainders from §4.1 | ~400 | DMA mechanics, task contexts, pinout detail, source-file references |

Total ≈ 2,465 lines. Three options:

- **(a) Component directories.** Create `Arm_Sensor_Hub/Documentation/` and `RaspberryPi_Sensor_Hub/Documentation/`. These are plain directories in this monorepo, not submodules, so this is a single-branch change. Requires amending the checklist's "component repositories remain unchanged" scope line. This is what the authority model contemplates, and it empties `docs/` completely.
- **(b) Keep in Karetao anyway.** Place them under `03_COMPONENTS/` with an explicit non-normative marker. This contradicts the authority model's component-ownership rule and risks exactly the "copy of the component implementation documentation" that `DOCUMENTATION_AUTHORITY_MODEL.md` § Component integration boundary prohibits. If chosen, the model should be amended first rather than departed from silently.
- **(c) Defer.** Leave these six items in `docs/` for a later component-scoped pass; `docs/` is not emptied this round.

**Recommendation: (a).** It is the only option that satisfies both the authority model and the goal of emptying `docs/`. Note that the Pi bring-up guide alone is 1,757 lines of pure host provisioning procedure — it is operational runbook material, not a Karetao system contract, and placing it under system authority would be hard to defend at review.

---

## 5. Conflicts found — resolve explicitly, do not silently merge

`05_REFACTORING_RULES.md` § Conflicts forbids resolving these by guessing. Each needs an owner's decision recorded in `07_DECISIONS/`.

- **C-1 — `DATA_READY` semantics.** `CONTRACT_V1_FREEZE.md` § DATA_READY: "HIGH means a complete response frame is staged and ready for the Raspberry Pi to clock." `protocols/spi-contract.md` §8 (armed-then-assert): "A frame merely staged in a software buffer but not yet DMA-armed is not sufficient." These are different signals. The freeze document claims authority over lower-level documents; the SPI contract is the later and more specific statement. **Subject is a system interface → Karetao decides.** The armed-then-assert model appears to be the intended resolution but this must be confirmed, not assumed, and the loser marked superseded.
- **C-2 — CAN bit rate.** `SYSTEM_REQUIREMENTS.md` SYS-CAN-001 and `CAN_SYSTEM_INTERFACE.md` both state 1 Mbps. `CAN_BIT_TIMING_EVIDENCE.md` records that the generated `MX_CAN1_Init()` currently produces 875 kbps with a 66.7% sample point, and the `.ioc` agrees. This is requirement-vs-implementation, not a documentation conflict, but the requirement documents currently give no hint that the implementation does not meet them. Record as an open implementation gap in `05_VERIFICATION/`.
- **C-3 — SPI frame: fixed or maximum?** `SPI_SYSTEM_INTERFACE.md` says "Fixed transaction frame: 512 bytes". `spi-contract.md` §17 says "512-byte maximum frame". Fixed and maximum are different contracts for the host driver. Resolve before the stub is expanded.
- **C-4 — Broken reference.** `docs/project/SYSTEM_DECISIONS.md` and `docs/project/README.md` both link to `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`, which does not exist. The register's §6 lists it as "Empty — no content yet". Either create it or repoint both references to the register. Trivial, but it is currently the only broken inbound link into `Documentation/**`.
- **C-5 — `docs/project/Open_Items_List.md`** describes itself as "the canonical register of project questions". The decision register §2 already carries a qualifying note about this. On archive, the self-description must be marked superseded so the archived copy cannot be read as a live competing register.

---

## 6. Sequence

Ordered so that nothing is removed before its replacement exists.

**WP-1 — Resolve the §4.4 scope decision and conflicts C-1 and C-3.** Blocks WP-3. C-2, C-4, C-5 can proceed in parallel.

**WP-2 — Fix `06_IMPLEMENTATION_CHECKLIST.md` scope lines** (archive exclusion, component-repos-unchanged) to match the agreed scope. Do this before the work, so the checklist stays a valid gate rather than being retrofitted.

**WP-3 — Build out `02_INTERFACES/`.** The largest and highest-value package: SPI system interface expansion, new payload schema document, TIME interface completion, CAN interface expansion. Each destination document carries a provenance line naming its legacy sources, matching the convention already used in `04_SAFETY/`.

**WP-4 — Build out `01_SYSTEM/` and `06_CONFIGURATION/`.** New `SYSTEM_LIFECYCLE.md`; complete `SYSTEM_ARCHITECTURE.md`; replace the `SYSTEM_OVERVIEW.md` placeholder; fold calibration and joint mapping into `SYSTEM_CONFIGURATION.md`.

**WP-5 — Complete `03_COMPONENTS/`.** System-visible component facts only: sensor topology table, interface pin assignments, MCU/clock constraints. Guard against this becoming a copy of the implementation docs.

**WP-6 — Component content** per the §4.4 decision.

**WP-7 — Archive.** Move §4.2 content into `99_ARCHIVE/` subdirectories, each with a header stating its historical status and what superseded it. Remove the `.gitkeep.md` files as real content lands.

**WP-8 — Verify before removal.** Per §7. Only then delete §4.3 stubs and remove `docs/`.

**WP-9 — Update entry points.** Root `README.md`, `Arm_Sensor_Hub/README.md`, `RaspberryPi_Sensor_Hub/README.md`, `00_INDEX.md` framework-status note, and `DOCUMENTATION_AUTHORITY_MODEL.md` § "Cross-document authority transition" — all currently describe `docs/project/**` as existing transitional material. They become wrong the moment `docs/` is removed.

WP-3, WP-4 and WP-5 touch disjoint files and can run concurrently once WP-1 closes.

---

## 7. Acceptance criteria

`docs/` may only be removed when all of the following hold:

1. **No orphaned statement.** Every normative or factual statement in `docs/project/**` is either represented in an authoritative document, present in `99_ARCHIVE/` marked historical, recorded as an open item in the register, or listed in a written "deliberately dropped" note with a reason. A per-file provenance ledger, produced as WP-8 runs, is the evidence.
2. **No new authority.** No Karetao document asserts ownership of a subject the authority model assigns elsewhere. Spot-check: no MKS protocol semantics restated as Karetao requirements; no component test result appearing as `SYSTEM_VERIFIED`; no vendor register map copied in.
3. **Verification separation holds.** Everything migrated from an evidence document (`CAN_BIT_TIMING_EVIDENCE.md`, `PHASE_1_FINAL_CLEARANCE_REPORT.md`, `CONTRACT_STATUS.md`) lands as evidence or as an open gate, never as a requirement. `SYSTEM_VERIFICATION_MATRIX.md` shows the same ten OPEN rows unless new accepted evidence justifies otherwise.
4. **Provisional stays provisional.** Values flagged provisional in the SYS-* table — 5 MHz SPI, 1 Mbps CAN, ±1 ms timestamp error, 500 Hz EKF — are not restated as settled anywhere in the expanded interface documents.
5. **Links resolve.** Every relative link in `Documentation/**` resolves, including C-4. No document links into `docs/`.
6. **Implementable from Karetao alone.** A reader can derive the full SPI wire format, the time model and the lifecycle state machine from `Documentation/**` without opening `docs/` or the component tree. This is the substantive test; criteria 1–5 are hygiene.

---

## 8. Risks

- **Bulk-move risk.** The authority model warns that moving a document into a directory does not make its contents authoritative for that directory. The firmware `_CONTRACT.md` files are the trap: fifteen plausible-looking contract documents, of which roughly half are component-internal. §3's boundary test must be applied per statement, not per filename.
- **Losing the caveats.** The legacy documents are unusually careful — "engineering calculation; not hardware validation", "these are firmware response levels, not a PL/SIL mapping", "the current 5 MHz value is an integration ceiling, not hardware approval". These qualifiers are the most valuable content in the tree and the easiest to drop when reformatting into a requirements table. Carry them verbatim.
- **Volume asymmetry.** `Documentation/**` will roughly triple. Review capacity, not authoring, is the constraint; WP-3 through WP-5 should be reviewed as they land rather than as one merge.
- **`docs/` removal is one-way in practice.** Content remains in git history, but nothing links to it. Criterion 1's ledger is what makes removal defensible later.
