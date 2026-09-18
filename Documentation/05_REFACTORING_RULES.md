# Documentation Refactoring Rules

These rules govern the later migration of existing documentation into the approved framework. This stage does not perform the migration.

## Inventory

Before moving anything, inventory documentation across Karetao, Arm Sensor Hub, Raspberry Sensor Hub, relevant submodules, and vendor/reference material. Include Markdown, README files, design documents, contracts, TODOs, sprint reports, decision records, conversation records, manuals, verification records, and other documentation-like files.

## Classification

Each document must receive one disposition: KEEP, MERGE, MOVE, ARCHIVE, or DELETE.

## Authority

For every normative statement determine its subject, owning repository, authoritative document, and whether the current document duplicates that authority.

## Requirements

System requirements belong in Karetao. Component implementation details remain in the component repository. Do not create competing copies of system requirements.

## Interfaces

Separate the system interface from the component implementation. A system interface defines what the system requires. A component document explains how that component implements it.

## Historical Material

Preserve historically useful material in `99_ARCHIVE/`. Archive material is non-normative.

## Deletion

Do not delete a document simply because it appears old. Before deletion inspect Git history, determine whether it contains unique information, identify whether its information has been migrated, and verify that no active documentation links to it.

## Vendor Material

Do not rewrite vendor specifications as project specifications. Reference them as external authority.

## Conflicts

Do not resolve conflicting requirements by guessing. Identify the conflict and resolve it against the applicable authority.

## Traceability

Important system requirements should remain traceable from system requirement → component implementation → verification evidence.

## Core Objective

The objective is not simply fewer files. The objective is fewer competing sources of truth while retaining useful information and traceability.
