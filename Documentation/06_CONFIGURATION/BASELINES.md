# Baselines

Role: configuration-management record. A baseline is a git tag that freezes a named set of
documents at a reviewed state. This document says which files each baseline covers and who
signs it. It defines no requirement; the files it names keep their own authority.

Tag pattern: `baseline/<name>/v<n>`. A new version is tagged when the covered files change
in a way the signer accepts as a new reviewed state; the tag's commit is the baseline.

| Baseline | Files covered | Signer | Versions |
|---|---|---|---|
| `requirements` | `01_SYSTEM/PROJECT_CHARTER.md`, `01_SYSTEM/SYSTEM_REQUIREMENTS.md`, `04_SAFETY/SAFETY_REQUIREMENTS.md`, `06_CONFIGURATION/PARAMETER_REGISTER.md` | Lenton Neale | none yet (the charter-alignment sign-off, `CHARTER_ALIGNMENT_PLAN.md` §3.9, is the first) |
| `architecture` | `01_SYSTEM/SYSTEM_ARCHITECTURE.md`, `02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`, `02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md`, `02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md`, `02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md`, `02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md` | Lenton Neale | `baseline/architecture/v1` |

To tag: `git tag -a baseline/<name>/v<n> -m "<what was reviewed>"` on `main`, then `git push --tags`.
To see what a baseline froze: `git show baseline/<name>/v<n> --stat`.

Provenance: the file lists were the `[lifecycle.files]` setting of the ICM Portal (`portal.toml`,
removed 2026-10-15 when the Portal was retired); the Portal's gate checks used them.
