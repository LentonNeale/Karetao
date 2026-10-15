# Domain Docs

> Agent configuration for the mattpocock-skills plugin. Not project documentation; `Documentation/DOCUMENTATION_RULES.md` and `Documentation/00_INDEX.md` are the authority.

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout: single-context, with Karetao's own files in place of `CONTEXT.md` and `docs/adr/`

The generic skills expect a `CONTEXT.md` glossary and `docs/adr/` decision records at the repo root. Karetao already has both roles filled inside `Documentation/`, which is the only documentation authority; a root `CONTEXT.md` or `docs/adr/` would be a competing copy, which the documentation rules forbid. **Do not create them.** Read these instead:

| Generic role      | Karetao file |
| ----------------- | ------------ |
| `CONTEXT.md` (vocabulary, scope) | `Documentation/00_INDEX.md`, then `Documentation/01_SYSTEM/PROJECT_CHARTER.md` (scope, goals, non-goals, who decides) and `Documentation/01_SYSTEM/SYSTEM_OVERVIEW.md` |
| `docs/adr/` (decision records) | `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md` (live decision log) and `Documentation/07_DECISIONS/KARETAO_DECISIONS_QUESTIONS_ISSUES_REGISTER.md` (full register; §0 is live work) |
| per-component context | `Arm_Sensor_Hub/Documentation/`, `RaspberryPi_Sensor_Hub/Documentation/` (implementation only; never redefine a system requirement) |
| numbers | `Documentation/06_CONFIGURATION/PARAMETER_REGISTER.md`; every value carries a basis: Measured, Datasheet, Derived, or Provisional |

Before working in an area, read the decisions and requirements that touch it. Requirement identifiers are `SYS-*`, decisions `SD-xx`, live work `LIVE-xx`; keep the traceability chain requirement → implementation → verification evidence → system verification.

## Use the authority's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as the Documentation defines it. In particular: "Provisional" is the word for an unconfirmed engineering estimate, never "guess" or "assumed"; items marked "proposed" or "open" are not decided; `SYSTEM_VERIFIED` is set only by the system verification matrix.

If the concept you need isn't defined, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## When `/domain-modeling` or `/grill-with-docs` wants to write

- A new or sharpened **term**: propose it for the owning document in `Documentation/` (the index says who owns which subject). Lenton decides.
- A new **decision**: draft it in the style of `ARCHITECTURE_DECISIONS.md` (Status, Decision, consequences, which requirement it changes) and add it to the register. Don't write a separate ADR file.
- Run `icm-project/tools/doc_check` before any documentation change is merged.

## Flag ADR conflicts

If your output contradicts a recorded decision, surface it explicitly rather than silently overriding:

> _Contradicts SYS-GATE-001 (motion gate inputs), but worth reopening because…_
