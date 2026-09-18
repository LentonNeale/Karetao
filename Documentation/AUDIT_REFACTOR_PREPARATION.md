# Karetao Documentation Audit — Refactor Preparation

**Audit status:** Complete for the observable repository baseline and indexed documentation set  
**Audit branch:** `doc/reconcile-karetao-mks`  
**Audit source commit observed before writing this record:** `239626d33b49ab1f66b40c8912a83e5e761bb713`  
**Refactor destination:** `doc/documentation-framework`  
**Date:** 2026-09-18

## 1. Purpose and phase boundary

This record is the persistent audit and refactor-preparation output for the Karetao documentation reconciliation.

The audit determines subject authority, content role, conflicts, preservation requirements, unresolved questions, and refactor requirements. It does not migrate, rewrite, delete, archive, or otherwise refactor the audited documentation.

The audit treats `doc/reconcile-karetao-mks` as the source/audit state. The later refactor destination is `doc/documentation-framework`.

The Karetao documentation framework is treated as the intended Karetao system-documentation authority structure. In particular, `Documentation/**` is the established framework and Karetao owns system-level requirements and definitions. The root README's `docs/project/` canonicality statement is legacy authority information and is not used to override that framework.

## 2. Repository state actually observable

No local Git working-tree state was assumed or used. Repository state was inspected through GitHub remote refs and file contents.

Observed refs:

- `doc/reconcile-karetao-mks` exists and currently resolves to `239626d33b49ab1f66b40c8912a83e5e761bb713`.
- `doc/documentation-framework` exists.
- The audit branch was not modified except for this audit artefact.
- No merge, rebase, reset, force-push, branch deletion, substitute branch creation, or destructive operation was performed.

The indexed documentation baseline records Karetao tree commit `bb473df6cf8df8f997181f3d02beeb143298d17a`, Arm Sensor Hub `main` at `a86f83036a3fb97450e661bf5b09557af4064274`, and RaspberryPi Sensor Hub `main` at `087e6c3e0b102c2e32dbf0dace30376e38b26123` in the index. The audit therefore distinguishes the indexed baseline from the current remote branch state where necessary.

## 3. Documentation inventory examined

The persistent index and content classification were used as the principal audit inventory.

The index records:

- 3 repositories: Karetao, Arm Sensor Hub, RaspberryPi Sensor Hub.
- 112 indexed documentation-like files in the Karetao tree.
- 156 indexed documentation-like entries in the complete cross-repository classification.
- Current `Documentation/**`, legacy `docs/project/**`, root documentation, and documentation-like files embedded in the repository tree.
- Component documentation from Arm Sensor Hub and RaspberryPi Sensor Hub.
- Vendor/external MKS documentation.
- Archived material under `docs/project/archive/**`.

For current-authority analysis, `docs/project/archive/**` is excluded. It remains historical reference material and is not promoted to current authority or ordinary migration input.

Material classes examined include:

- Karetao framework/governance documents;
- Karetao system architecture, requirements, interfaces, safety, verification, configuration, and decision records;
- legacy `docs/project/**` contracts and operational documents;
- Karetao and component READMEs;
- Arm implementation documentation;
- Raspberry implementation documentation;
- MKS/vendor references;
- verification and evidence records.

## 4. Authority model established by the framework

The current Karetao framework establishes separate authority domains rather than a universal directory hierarchy:

| Subject | Authority |
|---|---|
| Karetao system requirements | Karetao |
| Karetao system architecture | Karetao |
| Karetao system-level interfaces | Karetao |
| Karetao system timing/synchronization | Karetao |
| Karetao system safety requirements | Karetao / relevant safety authority boundary |
| Karetao system configuration requirements | Karetao |
| Karetao system verification status | Karetao verification process/matrix |
| Karetao component system definitions | Karetao |
| Arm implementation | Arm Sensor Hub |
| Raspberry implementation | RaspberryPi Sensor Hub |
| External equipment/protocol behaviour | Vendor/external authority |
| Verification evidence | Evidence record; evidence does not redefine requirements |

The framework explicitly states that physical location does not determine authority and that significant statements in mixed documents must be classified by subject.

## 5. Content-level classification findings

### 5.1 Governance/framework

The following current `Documentation/**` files are framework/governance material rather than evidence that their named destination already contains complete technical authority:

- `Documentation/00_INDEX.md`
- `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md`
- `Documentation/03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md`
- `Documentation/05_REFACTORING_RULES.md`
- `Documentation/06_IMPLEMENTATION_CHECKLIST.md`

Framework placeholders such as `SYSTEM_REQUIREMENTS.md`, `SYSTEM_ARCHITECTURE.md`, `SYSTEM_TIMING.md`, `SYSTEM_SYNCHRONIZATION.md`, and the system verification/configuration placeholders must not be treated as populated technical authority merely because of their filenames.

### 5.2 Karetao system-level content

The audit identifies system-level statements in legacy documents that should be preserved and reconciled into the Karetao authority domains. Examples include:

- system requirements recorded in `docs/project/SD/SD-03.md`, `SD-04.md`, `SD-05.md`, `SD-15.md`, `SD-18.md`, `SD-20.md`, `SD-24.md`, and `SD-25.md`;
- system architecture and runtime/data-flow material in `docs/project/system/architecture.md`;
- system/interface contract material in `docs/project/protocols/spi-contract.md`, `spi-payload-schema.md`, `docs/project/interfaces/raspberry-pi-spi.md`, and related mixed contracts;
- system lifecycle semantics and cross-service constraints in `docs/project/firmware/LIFECYCLE_CONTRACT.md`;
- system time/synchronization semantics in `docs/project/firmware/TIMESTAMP_SYNC_CONTRACT.md`;
- system safety/release-gate statements in `docs/project/firmware/SAFETY_RELEASE_CHECKLIST.md`;
- system-level component roles and responsibilities represented by the Karetao component documents/framework.

These statements are not all of the same authority. The later refactor must split system-facing clauses from implementation-specific clauses rather than moving whole mixed documents unchanged.

### 5.3 Component implementation and component interface content

The audit identifies Arm Sensor Hub implementation ownership for concrete firmware/service behavior, including:

- CAN service API, scheduling, queues, state behavior;
- I2C manager implementation;
- sensor acquisition and mux implementation;
- STM32 lifecycle implementation;
- SPI service/DMA ownership;
- MKS integration implementation;
- implementation configuration and diagnostics;
- component-level verification evidence.

RaspberryPi Sensor Hub owns its host-side implementation documentation.

Karetao retains ownership of the system-level definition of each component and the requirements placed on its interfaces.

### 5.4 External/vendor content

MKS manuals and related vendor material are external authority for MKS equipment/controller behaviour. The project-integrated MksServo README may contain both vendor-derived protocol information and project integration details; those statements must be separated by subject during refactoring.

Vendor behaviour must not be promoted into Karetao requirements.

### 5.5 Verification evidence

The audit identifies explicit verification evidence, including CAN timing evidence, phase/readiness reports, commissioning observations, and component-level test evidence.

Component verification is not equivalent to Karetao system verification. The framework identifies `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` as the authoritative Karetao system-level verification-status location; at the audited baseline it is a framework placeholder rather than a complete evidence record.

## 6. Material content that must be preserved

The later refactor should preserve, with provenance and appropriate reclassification:

1. System requirements and approved decision-derived requirements.
2. System interface semantics, including SPI transport/framing/time-model content.
3. Lifecycle and safety-gating semantics that are system-facing.
4. System timing and synchronization model.
5. System component roles and integration responsibilities.
6. Concrete component implementation information needed by component repositories.
7. Verification observations and their scope, including explicit validation gaps.
8. External MKS protocol/equipment facts with vendor provenance.
9. Decision records and rationale where they remain useful for traceability.
10. Historical material where needed to preserve provenance, while keeping it outside current authority.

## 7. Content that should be rewritten

The later refactor should rewrite, rather than mechanically move:

- legacy authority claims that `docs/project/` is the current canonical system documentation;
- mixed documents whose clauses cross system, component, configuration, and verification authority boundaries;
- framework placeholder text where substantive current content has been identified elsewhere;
- summaries that imply implementation status is system acceptance;
- references that point readers to obsolete documentation hierarchies;
- duplicate descriptions whose current authority is established elsewhere.

## 8. Content that should be consolidated

The following content families require consolidation into the Karetao framework where the subject is system-owned:

| Content family | Intended Karetao destination |
|---|---|
| System requirements extracted from decisions/contracts | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md` |
| System architecture and system component roles | `Documentation/01_SYSTEM/` and `Documentation/03_COMPONENTS/` |
| System interface contracts | `Documentation/02_INTERFACES/` |
| System timing/synchronization | `Documentation/01_SYSTEM/` |
| System safety requirements/architecture | `Documentation/04_SAFETY/` |
| System verification status/requirements | `Documentation/05_VERIFICATION/` |
| Controlled system configuration | `Documentation/06_CONFIGURATION/` |
| System decisions | `Documentation/07_DECISIONS/` |
| Historical/non-normative Karetao material | `Documentation/99_ARCHIVE/` |

These are refactor destinations, not actions authorized by this audit.

## 9. Content that should remain component-specific

Implementation details should remain in the owning component repository, including:

- STM32 driver/service implementation;
- concrete CanService/I2C/SPI implementation APIs;
- RTOS task and DMA ownership details;
- sensor-driver implementation;
- MKS codec integration implementation;
- Raspberry host implementation and deployment mechanics;
- component diagnostics and component-level verification evidence;
- component-specific build/configuration procedures.

Karetao should reference these implementations where needed rather than duplicate them as system authority.

## 10. Conflicts and authority-transition findings

### Conflict 1 — Root README authority claim

**Affected documentation:** Karetao `README.md`, Karetao `Documentation/00_INDEX.md`, `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md`, legacy `docs/project/README.md`.

**Evidence:** The root README currently states that `docs/project/` is the canonical project documentation and that all project-level engineering documentation is consolidated there. The framework states that Karetao owns system-level documentation through the `Documentation/**` framework.

**Conflict:** The README's current wording presents the legacy hierarchy as canonical while the framework establishes the new Karetao authority structure.

**Current assessment:** Legacy/current authority-transition statement. It is factual evidence of the old organization, but it must not override the framework.

**Required refactor decision:** Rebuild the root README so it no longer asserts `docs/project/` as current canonical system authority.

### Conflict 2 — Component README authority claims in the Karetao tree

**Affected documentation:** `Arm_Sensor_Hub/README.md`, `RaspberryPi_Sensor_Hub/README.md` as present in the Karetao audit tree.

**Evidence:** Both embedded READMEs point users to Karetao `docs/project/` as the canonical/current project documentation. The framework states that Karetao is authoritative for system documentation and that component repositories own implementation documentation.

**Conflict:** The links encode the obsolete `docs/project/` authority model.

**Current assessment:** Legacy navigation/authority conflict. The implementation content in these READMEs remains useful, but their documentation-governance statements are obsolete relative to the framework.

**Required refactor decision:** Replace legacy canonical-documentation claims with references consistent with the Karetao/component authority model. Coordinate with component repository state where the embedded tree is not identical to the standalone component repository.

### Conflict 3 — Legacy `docs/project/` self-identifies as canonical

**Affected documentation:** `docs/project/README.md` and its document table.

**Evidence:** It explicitly calls itself the canonical home for project-level engineering documentation and labels many legacy documents Active.

**Conflict:** This conflicts with the established Karetao `Documentation/**` framework.

**Current assessment:** The document is itself a legacy authority declaration. Its technical contents can remain evidence, but its canonicality claim is not current authority.

**Required refactor decision:** Remove/supersede the legacy authority claim as part of the later transition; preserve technical content by statement-level reconciliation.

### Conflict 4 — Mixed contracts combine system and component authority

**Affected documentation:** SPI, lifecycle, timestamp, CAN, sensor, calibration, build, safety, and related legacy contracts.

**Evidence:** The content classification identifies 45 mixed documents containing combinations of system contracts, component implementation, configuration, and verification evidence.

**Conflict:** Whole-document authority cannot safely be assigned to a single domain.

**Current assessment:** Statement-level splitting is required.

**Required refactor decision:** Extract system-owned clauses to Karetao, component-owned implementation to the relevant component repository, evidence to verification locations, and external behaviour to vendor references.

### Conflict 5 — Verification status boundary

**Affected documentation:** legacy contract/evidence documents versus `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`.

**Evidence:** The classification distinguishes component evidence from system verification and notes that the system verification matrix is a framework placeholder at the indexed baseline.

**Conflict/uncertainty:** Existing evidence may demonstrate component or target behaviour without establishing integrated system acceptance.

**Current assessment:** Do not upgrade component evidence to system verification.

**Required refactor decision:** Populate the system verification authority from appropriately scoped integration evidence; retain component evidence in component scope.

## 11. Open issues

### Issue 1 — Exact system requirement identifiers

**Affected documentation:** decision records and normative legacy contracts.

**Evidence:** Several decisions contain requirement-like statements, but existing documents do not provide one complete, stable system requirement identifier set.

**Conflict or uncertainty:** It is unclear which statements should become unique Karetao requirements versus design decisions, implementation constraints, or verification criteria.

**Current assessment:** Unresolved.

**Required refactor decision:** Define stable requirement identifiers and trace each promoted requirement to its source decision/contract.

### Issue 2 — System versus Arm implementation ownership of contract clauses

**Affected documentation:** mixed firmware contracts, especially CAN, SPI, lifecycle, sensor, calibration, and timestamp documents.

**Evidence:** The classification identifies both system-facing and component-facing clauses within the same documents.

**Conflict or uncertainty:** Some clauses express externally visible system behaviour while adjacent clauses specify STM32 implementation mechanisms.

**Current assessment:** Authority is resolvable by subject in many cases, but not every clause has sufficient contextual evidence for automatic separation.

**Required refactor decision:** Review significant clauses individually; preserve unresolved ownership rather than guessing.

### Issue 3 — Current accepted SPI maximum and physical acceptance

**Affected documentation:** `docs/project/protocols/spi-contract.md`, related SPI implementation/evidence records.

**Evidence:** The contract treats 5 MHz as an integration ceiling and explicitly states that live-host and physical acceptance remains outstanding.

**Conflict or uncertainty:** Software implementation exists, but physical signal integrity, GPIO timing, NSS behavior, sustained transactions, and real Pi↔STM32 acceptance are not fully evidenced.

**Current assessment:** 5 MHz must not be presented as hardware-approved maximum.

**Required refactor decision:** Preserve the ceiling/validation distinction and link future acceptance evidence when available.

### Issue 4 — Time synchronization semantics and implementation bounds

**Affected documentation:** `TIMESTAMP_SYNC_CONTRACT.md`, SPI contract, implementation.

**Evidence:** The one-way transaction-point model, five-second validity, direct offset stepping, and implementation bounds are documented, while two-way RTT/slewing are explicitly future enhancements.

**Conflict or uncertainty:** Some implementation constraints are configurable and component-owned while the shared time model is system-facing.

**Current assessment:** Split model from implementation limits.

**Required refactor decision:** Establish system time authority and validity semantics in Karetao; keep implementation mechanics and bounded acceptance logic in Arm documentation.

### Issue 5 — Safety evidence versus application controls

**Affected documentation:** safety release checklist, lifecycle/CAN/time/motor documents.

**Evidence:** The safety checklist states that firmware tests/builds do not substitute for hardware evidence or external safety assessment and that application controls are not an independent safety function.

**Conflict or uncertainty:** Existing application fail-closed behaviour could otherwise be mistaken for sufficient safety validation.

**Current assessment:** Safety evidence remains incomplete/blocked in the audited material.

**Required refactor decision:** Keep safety requirements and release gates distinct from implementation controls and require explicit evidence provenance.

### Issue 6 — MKS vendor authority versus project integration

**Affected documentation:** MKS manuals and MksServo project documentation.

**Evidence:** Vendor manuals define controller/protocol behaviour; project code/docs define integration.

**Conflict or uncertainty:** Some integrated README material combines vendor-derived facts with project implementation statements.

**Current assessment:** Split external facts from project-owned integration behaviour.

**Required refactor decision:** Retain vendor provenance and avoid promoting vendor behaviour into Karetao requirements.

### Issue 7 — Cross-repository README divergence

**Affected documentation:** embedded component READMEs in Karetao versus standalone component repository READMEs.

**Evidence:** The Karetao audit tree contains legacy canonical-documentation pointers. The currently fetched standalone Arm Sensor Hub `main` README instead points to component-owned technical reference/contract/onboarding documentation; the currently fetched standalone RaspberryPi Sensor Hub README does not contain the legacy `docs/project/` canonical claim.

**Conflict or uncertainty:** The embedded repository state and standalone repository heads are not necessarily identical snapshots.

**Current assessment:** Do not infer that all repositories have the same current documentation state.

**Required refactor decision:** Reconcile references against the actual component repository authority declarations and the version/submodule state used by Karetao.

### Issue 8 — Incomplete populated Karetao framework destinations

**Affected documentation:** current `Documentation/01_SYSTEM/**`, `02_INTERFACES/**`, `04_SAFETY/**`, `05_VERIFICATION/**`, `06_CONFIGURATION/**`.

**Evidence:** Several files are framework placeholders while substantive content remains in legacy mixed documents.

**Conflict or uncertainty:** The framework establishes intended authority locations, but those locations are not yet complete sources of technical truth.

**Current assessment:** Migration must be content-led, not filename-led.

**Required refactor decision:** Populate each authoritative destination from reconciled evidence before declaring the legacy source superseded.

### Issue 9 — Duplicate/overlapping SPI material

**Affected documentation:** legacy SPI protocol/service/payload documents and component SPI contracts.

**Evidence:** The classification identifies SPI transport, payload semantics, service ownership, timestamp semantics, and implementation details across multiple documents.

**Conflict or uncertainty:** Some duplicated statements differ in scope and authority rather than being literal duplicates.

**Current assessment:** Requires consolidation by subject.

**Required refactor decision:** Define one system-level interface authority per system contract and link component implementation details to it.

### Issue 10 — Archive boundary

**Affected documentation:** `docs/project/archive/**`.

**Evidence:** The repository contains extensive historical conversations, reports, stubs, and superseded material.

**Conflict or uncertainty:** Archived material may contain useful technical facts, but it is not current authority.

**Current assessment:** Historical only unless current authority is independently re-established.

**Required refactor decision:** Exclude archive content from ordinary authority determination and migration; retain only where needed for provenance/traceability.

## 12. Unresolved questions

The following questions remain open after repository evidence review:

1. Which exact statement set should receive the first stable Karetao system requirement identifiers?
2. Which mixed contract clauses are intentionally system requirements versus Arm implementation constraints?
3. Which existing measurements constitute integration evidence versus component evidence?
4. Which vendor-derived MKS behaviours have been independently verified on target hardware?
5. Which legacy documents are safe to supersede once their statement-level content has been incorporated into the framework?
6. What exact cross-repository reference/authority declaration should be used by the component repositories at the point of refactor?
7. Which current Karetao framework placeholders require substantive population before legacy sources can be considered superseded?

These questions should remain explicit until repository evidence or an approved project decision resolves them.

## 13. Refactor requirements

The later refactor on `doc/documentation-framework` should:

1. Treat Karetao `Documentation/**` as the system-documentation authority structure.
2. Rebuild the root README and remove the legacy `docs/project/` canonicality claim.
3. Remove or supersede legacy authority claims in component-facing Karetao READMEs.
4. Reconcile `docs/project/**` by content and statement authority rather than moving it wholesale.
5. Exclude `docs/project/archive/**` from current authority and ordinary migration.
6. Extract and preserve system requirements with explicit identifiers and provenance.
7. Populate system architecture, timing, synchronization, interface, safety, verification, configuration, and decision authorities from supported evidence.
8. Keep component implementation documentation in the owning component repositories.
9. Keep vendor protocol/equipment behaviour externally attributed.
10. Preserve verification scope and distinguish component verification, hardware evidence, integration evidence, and system verification.
11. Consolidate duplicate/overlapping system interface and contract content without losing provenance.
12. Establish stable cross-repository references between Karetao system definitions and component implementation documentation.
13. Mark superseded/legacy material explicitly before removal or archival.
14. Do not delete content merely because it appears obsolete unless its replacement and provenance are established.
15. Preserve unresolved uncertainty instead of manufacturing a single authoritative interpretation.

## 14. Audit actions taken

- Confirmed the two authoritative workflow branches exist.
- Read the current audit branch ref and observed its current commit.
- Read the Karetao documentation index and content-level classification.
- Read the Karetao documentation authority model and component documentation model.
- Inspected representative current framework documents.
- Inspected the root and component README authority statements.
- Inspected representative legacy system, SPI, lifecycle, time-synchronization, and safety documents.
- Inspected current standalone Arm Sensor Hub and RaspberryPi Sensor Hub READMEs for cross-repository context.
- Recorded conflicts, open issues, preservation requirements, and refactor requirements.
- Created this persistent audit record on the audit branch.

## 15. Actions explicitly not taken

- No documentation refactor.
- No migration to `doc/documentation-framework`.
- No modification of `doc/documentation-framework`.
- No deletion or silent archival of documentation.
- No modification of component repositories.
- No changes to source code, tests, generated files, or submodules.
- No merge, rebase, reset, force-push, branch deletion, or substitute branch creation.
- No promotion of archived material to current authority.
- No resolution of unresolved technical questions merely for consistency.

## 16. Provenance

Primary evidence:

- `Documentation/DOCUMENTATION_INDEX.md` on `doc/reconcile-karetao-mks`: indexed repositories, baseline commits, document inventory, archive boundary, and initial authority classifications.
- `Documentation/DOCUMENTATION_CONTENT_CLASSIFICATION.md` on `doc/reconcile-karetao-mks`: statement-level authority analysis, 45 mixed-document classifications, system requirements, architecture, interfaces, component implementation, safety, verification, configuration, decisions, historical content, and potential destinations.
- `Documentation/00_INDEX.md`: Karetao documentation framework and system authority.
- `Documentation/01_SYSTEM/DOCUMENTATION_AUTHORITY_MODEL.md`: normative authority domains and conflict-resolution model.
- `Documentation/03_COMPONENTS/COMPONENT_DOCUMENTATION_MODEL.md`: Karetao/component ownership boundary and verification distinction.
- `README.md`: current legacy documentation-authority claim.
- `Arm_Sensor_Hub/README.md` and `RaspberryPi_Sensor_Hub/README.md` in the Karetao audit tree: legacy component-facing canonical-documentation claims.
- `docs/project/README.md`: legacy canonical-home claim and document inventory.
- Representative legacy contracts and system documents cited throughout this record.
- Standalone component repository READMEs fetched from their current `main` refs, used only as cross-repository context.

The audit does not claim that a current technical fact is verified merely because it appears in a legacy document. Where the source itself records a validation gap, that gap is preserved.

## 17. Completion and next-phase gate

**Audit complete:** Yes, for the observable current branch state plus the indexed cross-repository documentation baseline.

**Subsequent refactor may proceed:** Yes, subject to the explicit open issues and unresolved questions in this record.

The next phase must operate on:

`doc/documentation-framework`

and must not treat this audit branch as the final documentation destination.
