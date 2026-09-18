# Documentation Refactoring Rules

These rules govern the audit-derived documentation refactor into the approved framework. The framework is now the active destination; legacy content remains source/provenance material until its authoritative content has been reconciled.

## Inventory

Before moving anything, inventory documentation across Karetao, Arm Sensor Hub, Raspberry Sensor Hub, relevant submodules, and vendor/reference material. Include Markdown, README files, design documents, contracts, TODOs, sprint reports, decision records, conversation records, manuals, verification records, and other documentation-like files.

## Classification

Each document must receive one disposition: KEEP, MERGE, MOVE, ARCHIVE, or DELETE.

A legacy document may contain information belonging to multiple authority domains. Do not assign authority to the whole legacy document merely because it has a single filename or is moved into a particular directory.

For mixed-authority documents, classify each significant normative or factual statement by subject authority. Where necessary, split the information into system requirements, system architecture/interface definitions, component implementation, external/vendor references, verification evidence, and historical context.

## Authority

For every normative statement determine:

- its subject;
- the authority domain owning that subject;
- the authoritative document or record;
- whether the current content duplicates, summarizes, or conflicts with that authority.

Authority is determined by subject ownership. A document's physical location does not by itself make it authoritative.

## Requirements

System requirements belong in Karetao. Component implementation details remain in the component repository. Do not create competing copies of system requirements.

Moving an old document into a system documentation directory does not automatically make all of its contents Karetao system requirements.

## Interfaces

Separate the system interface from the component implementation. A system interface defines what the system requires. A component document explains how that component implements it.

## Verification

Component verification evidence is not the same as Karetao system verification. `SYSTEM_VERIFIED` is a Karetao system-level status established through the Karetao system verification process and [`Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md`](05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md), which is the authoritative location for that status.

## Historical Material

Preserve historically useful material in `99_ARCHIVE/`. Archive material is non-normative.

## Deletion

Do not delete a document simply because it appears old. Before deletion inspect Git history, determine whether it contains unique information, identify whether its information has been migrated, and verify that no active documentation links to it.

## Vendor Material

Do not rewrite vendor specifications as project specifications. Reference them as external authority.

## Conflicts

Do not resolve conflicting requirements by guessing. Identify the subject of the conflict, determine the authority domain that owns it, and resolve the conflict against that authority.

## Traceability

Important system requirements should remain traceable from system requirement → component implementation → verification evidence → Karetao system verification.

During migration, the required sequence is:

1. identify the subject of each normative or factual statement;
2. identify the authority owning that subject;
3. migrate the information to the appropriate authoritative location;
4. replace duplicated requirements with references to the authoritative requirement;
5. preserve useful historical context in the appropriate archive when necessary.

This migration sequence governs the active audit-derived documentation refactor on this branch.

## Core Objective

The objective is not simply fewer files. The objective is fewer competing sources of truth while retaining useful information and traceability.
