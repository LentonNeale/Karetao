# Evidence — cloud (CONN-R phase B)

**Source:** `digest-cloud-2026-09-25.json` (1 interactive session plus 13 subagent transcripts), and the token logs in `plans/icm-gui-fieldfix-plan.md` and the prototype plan.

1. **Main-session context dominates.** Opus: 375 messages and 85.8M cache_read, which is ≈229k per message. Every orchestrator turn re-reads the whole conversation (plans, diffs, reports). Removing orchestrator turns, or starting fresh sessions per phase with state kept in files, saves the most.
2. **Subagents read whole plans.** The 8k-token plan was read 13× (R3, L1–L4), once per work package, although each needed only the shared contract plus one WP section (~2–3k). `agents/haiku-dev.md` was read 13× (R2), which is expected.
3. **Rework on a boundary.** 2 of 11 Haiku WPs (the policy rules and the server routing) needed a Sonnet rework, ≈163k tokens in total. Both were threading or policy code, where Haiku drifted from the contract (defects D1, D2).
4. **Estimates were too low.** Haiku WPs ran 52–101k against budgets of 60–100k, usually 10–25% over.
5. **Late defects.** D5 (wrong walkthrough names, a disabled Approve button) reached the User's manual test, and cost 3 extra orchestrator rounds plus the User's time. A deliverable (the walkthrough) wasn't checked against the real files before hand-over.
6. **Repeated test-file reads.** `tests/gui/smoke.py` was read 15× (R1, ~21k), by subagents appending tests to a large shared file.
