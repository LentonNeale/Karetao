# Requester profile

How requests for Karetao are usually made, for the Client Liaison. Edit freely; keep it short.

- **Who:** the project's maintainer, an electronics and computer engineer working on a personal
  robotic-arm project.
- **Aim:** keep the project on good engineering practice: requirements traceability, recorded
  decisions, and verification evidence before anything is called done.
- **Scope:** hobby level; one maintainer, attended operation, no PL/SIL claim. Goals,
  non-goals and who decides (Lenton Neale) are in
  `Documentation/01_SYSTEM/PROJECT_CHARTER.md`; numeric values need a basis (Measured,
  Datasheet, Derived or Provisional).
- **Authority:** `Documentation/**` is the system authority (start at `Documentation/00_INDEX.md`);
  a request that would change a requirement, interface or safety rule goes there first.
- **Current work:** the documentation alignment plan at `Documentation/CHARTER_ALIGNMENT_PLAN.md`, run as agile sprints; stories are in `icm-project/backlog.json`.
- **Work packages:** `icm-project/lifecycle.json` (Project tab: Work, Lifecycle, Map). WP1 is the documentation
  alignment; its PASS at the Requirements gate is the sign-off. WP2 to WP6 are the code-alignment
  Stages 1 to 5 (fitted encoders, motor positions and timestamps, links measured, gated motion
  X/Y/Z, remaining joints). A new request for one of them is a run in that package.
- **Output fixes:** for a fix that changes printed output, ask which exact text a test should check.
- **Style:** plain language; short questions, a few at a time.
