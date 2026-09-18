# Legacy Project Documentation

> **Transitional status:** `docs/project/**` is legacy source material and is not the current Karetao documentation authority. Current Karetao system documentation is authoritative under [`Documentation/`](../../Documentation/), starting with [`Documentation/00_INDEX.md`](../../Documentation/00_INDEX.md).

This tree is retained during reconciliation so that technical statements, decisions, provenance and historical context are not silently lost.

## Current authority

Use `Documentation/**` for Karetao system-level:

- requirements;
- architecture;
- interfaces;
- timing and synchronization;
- safety;
- configuration;
- system verification;
- system-level component roles;
- current decision destinations.

Component repositories remain authoritative for component implementation.

## Legacy source use

Documents under this tree may contain mixed system, component, external-reference, decision and verification content. Their directory location does not establish authority. During reconciliation, content is separated by subject and traced to its authoritative destination.

The historical decision records under `SD/` remain important provenance. Requirement-bearing system statements are reconciled into `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md`; the decision records retain their decision status and rationale.

## Archive

`docs/project/archive/**` is historical/archived material and is excluded from current authority determination and ordinary migration.
