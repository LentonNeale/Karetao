# Board — ICM GUI

**Coordination PR:** #4 (draft, never merged) · **Contract:** `agent-work/CONTRACT.md` v1 · **Plans:** `agent-work/plans/`

**Plan approval:** `icm-gui-fieldfix-plan.md` is **proposed**, not yet approved by the User. Open questions for the User: the stage 01 status `accepted`, and C2 at T1. `icm-gui-chat-plan.md` is **proposed**; it follows the fieldfix plan.

## Work packages

| WP | Plan | Owner | Status | Approved | Branch / PR | Budget | Used | Notes |
|---|---|---|---|---|---|---|---|---|
| CONN | this contract | both | in-progress | yes (User asked for the connection test) | `agent-work/icm-gui` / #4 | 20k | | Handshake: local HELLO → cloud ACK → local CONNECTED |
| WP0 | fieldfix | cloud | proposed | no | `icm-gui-prototype` | 5k | | Merge `main` a60f2ff |
| FF1a | fieldfix | cloud | proposed | no | `icm-gui-prototype` | 15k | | Workspace contracts; User CHECKPOINT on the diff |
| FF1b | fieldfix | cloud | proposed | no | | 100k | | Also the "empty tier" rule (moved from FF2) |
| FF5 | fieldfix | cloud | proposed | no | | 60k | | |
| FF3 | fieldfix | cloud | proposed | no | | 90k | | |
| FF4 | fieldfix | cloud | proposed | no | | 40k | | |
| FF2 | fieldfix | **local** (proposed) | proposed | no | `field-fix/karetao-ff2` | 80k | | Needs real `gh`; new files only |
| LIAISON-9 | fieldfix Wave 5 | **local** | proposed | no | — | 30k | | Run all 9 liaison scenarios after FF1a merges; post the results in `results/` |
| FIELD-R2 | fieldfix Wave 5 | **local** | proposed | no | `field-feedback/karetao` | — | | Field re-test round 2 |
| CHAT-WP1 | chat | **local** (proposed) | proposed | no | `field-fix/karetao-chat-wp1` | 80k | | Record the real CLI protocol and fixtures on a clean machine (§WP1) |
