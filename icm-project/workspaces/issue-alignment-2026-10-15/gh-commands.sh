#!/usr/bin/env bash
# DRAFT, NOT EXECUTED. Proposed GitHub changes from the 2026-10-15 issue alignment check.
# Review each block; run blocks one at a time. Authority order for any conflict:
# PARAMETER_REGISTER.md and ARCHITECTURE_DECISIONS.md, then GitHub issues.
# Project-board actions are comment lines only (gh has no project scope here).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO=LentonNeale/Karetao

# ---------------------------------------------------------------------------
# 1. #42 [LIVE-19]: body predates the rulings. Evidence: body step 1 (link_stale) moved to #64
#    by R22; step 6 (DIAGNOSTIC v2) replaced by R14(d); step 8 (keep drift check) reversed by R16;
#    all five "open parameters" answered by R14, R16, R22 (ARCHITECTURE_DECISIONS.md, "Code-review
#    rulings", d068def); body cites retired SYS-FAIL-001 / SYS-SYNC-002 (SYSTEM_REQUIREMENTS.md lines
#    43, 52); parent #46 closed as not planned.
gh issue edit 42 --repo $REPO --body-file "$DIR/body-42.md"

# 2. #42: corrections to the Agent Brief comment (04:33 UTC). Evidence: TIME_SYSTEM_INTERFACE.md
#    section 3 (T2 = STM32 receipt, T4 = Pi receipt) vs the brief's "T4 on the STM32 side"; #64 owns
#    link_stale as B107 not B106/B110; B95 depends on B88; B128 removes the sync-quality fields that
#    B96 also names; Issue #12 item 4 and SPI_SYSTEM_INTERFACE.md section 13 vs B94/B130 hook design;
#    R16 row has no sub-letters or guard behaviour.
gh issue comment 42 --repo $REPO --body-file "$DIR/comment-42-brief-corrections.md"

# 3. #45 [LIVE-19]: body lists five gaps that the 2026-09-25 and 2026-10-15 comments call moot.
#    Replace with the removal half (R16). No work-package or story IDs added (Map retired).
gh issue edit 45 --repo $REPO --body-file "$DIR/body-45.md"

# 4. #28 [LIVE-08]: body still makes calibration a motion-gate prerequisite, withdrawn by D-3
#    (ARCHITECTURE_DECISIONS.md "Motion gate"); defers per R26; SYS-CAL-002 merged into SYS-CAL-001
#    (SYSTEM_REQUIREMENTS.md line 58).
gh issue edit 28 --repo $REPO --body-file "$DIR/body-28.md"

# 5. #47 [LIVE-08]: body cites "release conditions" and Arm_Sensor_Hub#5-#6, removed by the charter.
gh issue edit 47 --repo $REPO --body-file "$DIR/body-47.md"

# 6. #13 [LIVE-09]: body cites Documentation/05_VERIFICATION/INTEGRATION_GATES.md (does not exist;
#    last in de29f3b) and "release blockers".
gh issue edit 13 --repo $REPO --body-file "$DIR/body-13.md"

# 7. #32 [LIVE-22]: body is EKF-scoped (LIVE-07 closed not planned; charter non-goal), cites missing
#    Documentation/01_SYSTEM/SYSTEM_TIMING.md, and carries labels design + estimation.
#    estimation is dormant (ISSUE_CONTRACT.md); the work is verification + timing (contract examples:
#    "Link measurement -> verification + timing").
gh issue edit 32 --repo $REPO --body-file "$DIR/body-32.md"
gh issue edit 32 --repo $REPO --add-label verification --remove-label design --remove-label estimation

# 8. #61 [LIVE-18]: B79 text points drive settings at SYSTEM_CONFIGURATION.md section 2.1; the settings
#    now live in section 2.2 (lines 97-99, 85bb37e) with decisions "MKS drive work mode" (4aa2200) and
#    "MKS drive settings" (85bb37e). Adds those references.
gh issue edit 61 --repo $REPO --body-file "$DIR/body-61.md"

# 9. #62 [LIVE-18]: scope says position "following commanded motion" at Stage 2; R28(c) says Stage 2
#    shows positions at rest and turned by hand, commanded motion is evidenced at Stage 4.
gh issue edit 62 --repo $REPO --body-file "$DIR/body-62.md"

# 10. #63 [LIVE-20]: omits the motor command module (B109) and the MKS motion-commands and
#     multi-motor-synchronisation decisions (4aa2200); adds the B132 dependency (79050a4).
gh issue edit 63 --repo $REPO --body-file "$DIR/body-63.md"

# 11. #64 [LIVE-20]: B107 (count-based link_stale) and B112 (fault visibility) are in its scope text
#     but not in its story list or triage line.
gh issue edit 64 --repo $REPO --body-file "$DIR/body-64.md"

# 12. #66 [LIVE-17]: note that B72/B133 satisfy the timestamp item and that B128 replaces
#     SensorLatestValue_SetNotFitted (79050a4).
gh issue edit 66 --repo $REPO --body-file "$DIR/body-66.md"

# 13. #67 [LIVE-17]: scope item 3 says "one axis marked not fitted"; SYSTEM_CONFIGURATION.md section 2.1
#     already records axes 0 and 3 as not fitted (4aa2200).
gh issue edit 67 --repo $REPO --body-file "$DIR/body-67.md"

# ---------------------------------------------------------------------------
# OPTIONAL (minor): titles outside the preferred verbs of ISSUE_FRAMEWORK.md 3.2.
# gh issue edit 64 --repo $REPO --title "[LIVE-20] Implement the motion gate at D-3 (SYS-GATE-001)"
# gh issue edit 66 --repo $REPO --title "[LIVE-17] Implement the NOT_FITTED host tests and tooling (C, Python, tests)"
# gh issue edit 32 --repo $REPO --title "[LIVE-22] Verify per-axis acquisition timing and latency"
# gh issue edit 47 --repo $REPO --title "[LIVE-08] Verify the calibration and configuration evidence"

# ---------------------------------------------------------------------------
# LABEL DRIFT: repo labels differ from the ISSUE_CONTRACT.md table (colour or description).
# Evidence: gh label list 2026-10-15 (design #ef250d vs #0E7490; communications and configuration
# #ededed vs #0891B2 and #64748B; safety, communications, configuration have no description;
# estimation description is not the "dormant" text).
gh label edit design --repo $REPO --color 0E7490
gh label edit communications --repo $REPO --color 0891B2 --description "CAN, SPI, transport, protocols, messaging, or communication interfaces."
gh label edit configuration --repo $REPO --color 64748B --description "Calibration, parameters, configuration data, persistence, versioning, or validity."
gh label edit safety --repo $REPO --description "Safety mechanisms, boundaries, hazards, controls, or safety evidence."
gh label edit estimation --repo $REPO --description "Dormant since 2026-10-03: state estimation is a charter non-goal. Do not apply."

# ---------------------------------------------------------------------------
# PROJECT BOARD (users/LentonNeale/projects/4, reopening 2026-10-15). Comment lines only.
# Proposed Status follows each issue's triage state; order is the proposed manual order within a
# milestone (dependencies first). Lenton to confirm.
#   Stage 1 Fitted encoders:   #66 Ready (ready-for-agent); #67 Backlog (bench, ready-for-human)
#   Stage 2 Motor positions:   #61 Ready; #42 Ready; #45 Backlog (closes with #42); #62 Backlog (bench)
#   Stage 3 Links measured:    #32 Backlog (bench)
#   Stage 4 Gated motion:      #64 Ready (needs the requirements amendment first); #63 Ready; #65 Backlog (bench)
#   No milestone (after Stage 4, ruling R26): #28 Backlog; #47 Backlog; #13 Backlog
#   Add all 13 open issues to the board; #61-#67, #42, #45, #28, #47, #13, #32.

# ---------------------------------------------------------------------------
# CLOSED-ISSUE HOUSEKEEPING (Lenton's rulings 2026-10-15, grilling round).
# #24 is closed as "completed" but its requirement (SYS-SYNC-002 applied to all motion) was withdrawn by D-3;
# "not planned" is the accurate reason. gh issue close on a closed issue only changes the reason.
gh issue close 24 --repo $REPO --reason "not planned"
# Stale closing comments: #43 predates R9 (1 Mbit/s decided); #22 and #29 say "heartbeat if ruled" but R23 ruled it;
# #22 names B111 for motor_ready where B131 now owns it.
gh issue comment 43 --repo $REPO --body-file "$DIR/comment-43.md"
gh issue comment 22 --repo $REPO --body-file "$DIR/comment-22.md"
gh issue comment 29 --repo $REPO --body-file "$DIR/comment-29.md"
