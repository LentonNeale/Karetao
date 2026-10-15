#!/usr/bin/env bash
# Migrates backlog stories of Stage 0 (WP9) and Stage 1 (WP10) into GitHub issues.
# NOT YET RUN. Review it, then run it once from any directory: bash gh-commands.sh
# It is not idempotent: a second run would create duplicate issues. See README.md.
set -euo pipefail

REPO=LentonNeale/Karetao
DIR="$(cd "$(dirname "$0")" && pwd)"

# Database id of an issue number (the dependencies endpoint takes the id, not the number).
dbid() { gh api "repos/$REPO/issues/$1" --jq .id; }

# edge CHILD BLOCKER: records "CHILD is blocked by BLOCKER" (native issue dependency).
edge() {
  gh api --method POST "repos/$REPO/issues/$1/dependencies/blocked_by" -F issue_id="$(dbid "$2")" >/dev/null
  echo "#$1 <- #$2"
}

# --- Preflight: fail before creating anything ---
gh auth status >/dev/null
existing="$(gh api "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')"
for m in 'Stage 1 — Fitted encoders'; do
  grep -qxF -- "$m" <<<"$existing" || { echo "missing milestone: $m" >&2; exit 1; }
done
if grep -qxF -- 'Stage 0 — Foundation' <<<"$existing"; then echo "milestone already exists: Stage 0 — Foundation" >&2; exit 1; fi

# === a. Milestone ===
gh api --method POST "repos/$REPO/milestones" \
  -f title='Stage 0 — Foundation' \
  -f description='Firmware identity at build time, task stack sized and checked, golden-frame vectors, restored codec tests, the evidence-record tool, one parameter header and CI hardening, all before any bench run.'

# === b. Issues (WP9 -> Stage 0 — Foundation, WP10 -> Stage 1 — Fitted encoders) ===
ISSUE_B55=$(gh issue create --repo "$REPO" --title 'Implement shared golden-frame vectors asserted by the C and Python SPI suites' --body-file "$DIR/body-B55.md" --milestone 'Stage 0 — Foundation' --label verification --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B56=$(gh issue create --repo "$REPO" --title 'Verify the MksServo codec against the MKS manual by restoring its host tests' --body-file "$DIR/body-B56.md" --milestone 'Stage 0 — Foundation' --label verification --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B57=$(gh issue create --repo "$REPO" --title 'Implement the evidence-record tool with firmware VERSION identity and Pi commit' --body-file "$DIR/body-B57.md" --milestone 'Stage 0 — Foundation' --label implementation --label verification | tail -1 | grep -oE '[0-9]+$')
ISSUE_B58=$(gh issue create --repo "$REPO" --title 'Update the host-test harness: NDEBUG guard, CAN TX log, deeper I2C scripts, real time_service' --body-file "$DIR/body-B58.md" --milestone 'Stage 0 — Foundation' --label verification | tail -1 | grep -oE '[0-9]+$')
ISSUE_B59=$(gh issue create --repo "$REPO" --title 'Remove dead Pi tests and the TIME_SYNC echo decoder' --body-file "$DIR/body-B59.md" --milestone 'Stage 0 — Foundation' --label implementation --label verification | tail -1 | grep -oE '[0-9]+$')
ISSUE_B60=$(gh issue create --repo "$REPO" --title 'Update CI: doc_check job, lockstep cross-triggers, map upload, warnings as errors, pinned toolchain' --body-file "$DIR/body-B60.md" --milestone 'Stage 0 — Foundation' --label implementation | tail -1 | grep -oE '[0-9]+$')
ISSUE_B61=$(gh issue create --repo "$REPO" --title 'Implement one firmware parameter header and one Pi config module mirroring the parameter register' --body-file "$DIR/body-B61.md" --milestone 'Stage 0 — Foundation' --label implementation --label configuration | tail -1 | grep -oE '[0-9]+$')
ISSUE_B62=$(gh issue create --repo "$REPO" --title 'Update Pi packaging and fix small SPI adapter defects' --body-file "$DIR/body-B62.md" --milestone 'Stage 0 — Foundation' --label implementation | tail -1 | grep -oE '[0-9]+$')
ISSUE_B63=$(gh issue create --repo "$REPO" --title 'Implement doc_check extensions: matrix trace, retired IDs, section references, index coverage' --body-file "$DIR/body-B63.md" --milestone 'Stage 0 — Foundation' --label implementation | tail -1 | grep -oE '[0-9]+$')
ISSUE_B64=$(gh issue create --repo "$REPO" --title 'Remove dead and duplicated firmware code, including the ISR mutex-give async I2C path' --body-file "$DIR/body-B64.md" --milestone 'Stage 0 — Foundation' --label implementation | tail -1 | grep -oE '[0-9]+$')
ISSUE_B130=$(gh issue create --repo "$REPO" --title 'Implement the Pi ExchangeSession with a firmware-rules fake and a process-wide Sequencer' --body-file "$DIR/body-B130.md" --milestone 'Stage 0 — Foundation' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B134=$(gh issue create --repo "$REPO" --title 'Implement a build-time check of the main (interrupt) stack depth' --body-file "$DIR/body-B134.md" --milestone 'Stage 0 — Foundation' --label implementation | tail -1 | grep -oE '[0-9]+$')
ISSUE_B128=$(gh issue create --repo "$REPO" --title 'Implement the latest-value store that owns sample and feedback ageing and the coherent snapshot copy' --body-file "$DIR/body-B128.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label timing | tail -1 | grep -oE '[0-9]+$')
ISSUE_B65=$(gh issue create --repo "$REPO" --title 'Implement GET_SNAPSHOT answered with a correlated SNAPSHOT of sensor and motor records' --body-file "$DIR/body-B65.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B132=$(gh issue create --repo "$REPO" --title 'Update the SPI response path so spi_protocol.c validates and builds every response and the service is transport only' --body-file "$DIR/body-B132.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B133=$(gh issue create --repo "$REPO" --title 'Implement the AS5600 sample in two bus reads with a typed magnet condition' --body-file "$DIR/body-B133.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label timing | tail -1 | grep -oE '[0-9]+$')
ISSUE_B66=$(gh issue create --repo "$REPO" --title 'Update the SPI service re-arm, stall and NSS-resync handling' --body-file "$DIR/body-B66.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B67=$(gh issue create --repo "$REPO" --title 'Implement DATA_READY armed-then-assert on the STM32 with a fresh-edge wait on the Pi' --body-file "$DIR/body-B67.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B68=$(gh issue create --repo "$REPO" --title 'Implement the Pi snapshot logger and probe output for Stage 1 evidence' --body-file "$DIR/body-B68.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B69=$(gh issue create --repo "$REPO" --title 'Update sequence seeding across processes and add a host resync rule' --body-file "$DIR/body-B69.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B70=$(gh issue create --repo "$REPO" --title 'Define the GET request payload and padding rule and apply them on both sides' --body-file "$DIR/body-B70.md" --milestone 'Stage 1 — Fitted encoders' --label design --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B71=$(gh issue create --repo "$REPO" --title 'Implement the snapshot flags bit and SPI transport counters' --body-file "$DIR/body-B71.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label communications | tail -1 | grep -oE '[0-9]+$')
ISSUE_B73=$(gh issue create --repo "$REPO" --title 'Implement sensor path hardening: bus recovery, bring-up retry, timeout diagnostics' --body-file "$DIR/body-B73.md" --milestone 'Stage 1 — Fitted encoders' --label implementation | tail -1 | grep -oE '[0-9]+$')
ISSUE_B74=$(gh issue create --repo "$REPO" --title 'Update the sensor policy: magnet warnings, processed-angle source, sweep counter' --body-file "$DIR/body-B74.md" --milestone 'Stage 1 — Fitted encoders' --label implementation --label configuration | tail -1 | grep -oE '[0-9]+$')
ISSUE_B77=$(gh issue create --repo "$REPO" --title 'Update ENCODER_BENCH_PROCEDURE to cover SYS-ENC-002 and link it from the index and matrix' --body-file "$DIR/body-B77.md" --milestone 'Stage 1 — Fitted encoders' --label verification | tail -1 | grep -oE '[0-9]+$')
ISSUE_B78=$(gh issue create --repo "$REPO" --title 'Remove data_ready_analysis.py and its unbased verdicts' --body-file "$DIR/body-B78.md" --milestone 'Stage 1 — Fitted encoders' --label implementation | tail -1 | grep -oE '[0-9]+$')

# === c. Dependencies (child <- blocker) ===
# c1. Graph v1 among the existing open issues
edge 67 66
edge 62 61
edge 42 61
edge 42 66
edge 45 42
edge 32 42
edge 32 62
# #66 carries stories B72, B75 and B76 (Lenton 2026-10-15): record their origin on it instead of creating issues.
gh issue view 66 --repo "$REPO" --json body --jq .body > "$DIR/.body-66.current"
{ echo 'Origin: backlog stories B72, B75, B76 (WP10); B72 is satisfied by B133.'; echo; cat "$DIR/.body-66.current"; } > "$DIR/.body-66.new"
gh issue edit 66 --repo "$REPO" --body-file "$DIR/.body-66.new"
rm -f "$DIR/.body-66.current" "$DIR/.body-66.new"

edge 63 61
edge 63 66
edge 64 63
edge 65 63
edge 65 64
edge 65 62
edge 28 65
edge 47 28
edge 13 65
edge 13 32
edge 13 47

# c2. Between the new issues. Each edge cites the sentence it comes from.
# B130 acceptance: "Depends on S9.4 (B55) for the golden vectors"
edge "$ISSUE_B130" "$ISSUE_B55"
# B62 acceptance: "Depends on S9.14 (B130)"
edge "$ISSUE_B62" "$ISSUE_B130"
# B65 acceptance: "Depends on S9.2 and S10.15 (B128): the SNAPSHOT is built from the latest-value store's coherent copy" (S9.2 is done)
edge "$ISSUE_B65" "$ISSUE_B128"
# B132 acceptance: "Depends on S10.15 (B128) and S10.1 (B65)"
edge "$ISSUE_B132" "$ISSUE_B128"
# B132 acceptance: "Depends on S10.15 (B128) and S10.1 (B65)"
edge "$ISSUE_B132" "$ISSUE_B65"
# B66 acceptance: "Depends on S10.16 (B132)"
edge "$ISSUE_B66" "$ISSUE_B132"
# B67 acceptance: "Depends on S10.2 (B66)" and "Depends on S10.2 (B66) and S10.16 (B132) for the single armed truth"
edge "$ISSUE_B67" "$ISSUE_B66"
# B67 acceptance: "Depends on S10.2 (B66) and S10.16 (B132) for the single armed truth"
edge "$ISSUE_B67" "$ISSUE_B132"
# B68 acceptance: "Depends on S10.1"
edge "$ISSUE_B68" "$ISSUE_B65"
# B68 acceptance: "Depends on S9.14 (B130)"
edge "$ISSUE_B68" "$ISSUE_B130"
# B69 acceptance: "Depends on S9.14 (B130)"
edge "$ISSUE_B69" "$ISSUE_B130"
# B70 acceptance: "Depends on S10.16 (B132)"
edge "$ISSUE_B70" "$ISSUE_B132"
# B71 acceptance: "Depends on S10.1"
edge "$ISSUE_B71" "$ISSUE_B65"
# B73 acceptance: "Depends on S10.17 (B133)"
edge "$ISSUE_B73" "$ISSUE_B133"
# B133 acceptance: "S10.9 (B73) and S10.10 (B74) point at it" (B74 also says its sweep counter is the instrument for re-measuring after B133). B74 -> B128 is implied through B133 -> B128, so not added separately
edge "$ISSUE_B74" "$ISSUE_B133"
# B133 acceptance: "Depends on S10.15 (B128)"
edge "$ISSUE_B133" "$ISSUE_B128"
# No edge: the evidence-record story names "Depends on S9.1" (build-time firmware identity), which is done.
# No edge: the snapshot story also names "S9.2" (task stack size), which is done.

# c3. From the new issues to existing ones
# Existing issue (child) blocked by a new issue (blocker); these edges come from the migration request.
edge 66 "$ISSUE_B128"
edge 66 "$ISSUE_B132"
edge 42 "$ISSUE_B55"
edge 42 "$ISSUE_B130"
edge 42 "$ISSUE_B132"
edge 63 "$ISSUE_B132"
edge 61 "$ISSUE_B55"
# Suggestion, not applied: #63 names "depends on stories B55 and B132" in its own criteria, so #63 <- B55 may also be wanted:
# #63 acceptance criteria: "depends on stories B55 and B132" (Lenton 2026-10-15: add the edge)
edge 63 "$ISSUE_B55"
# pending WP11 migration: #61 <- B88 (Pi motor-record decode) and #61 <- B131 (drive protocol module); #61's own scope lists both
# pending WP11 migration: new issues blocking later stories: B128 blocks B81; B132 blocks B89
# pending WP12 migration: B130 blocks B94; B132 blocks B93
# pending WP13 migration: B130 blocks B100
# pending WP14 migration: B132 blocks B108 and B111
# pending WP17 migration: #64 <- B126 (requirement amendment for stop-and-hold)

# === d. Board Status to set by hand (gh has no project scope here) ===
# ISSUE_B55: Ready
# ISSUE_B56: Ready
# ISSUE_B57: Ready
# ISSUE_B58: Ready
# ISSUE_B59: Ready
# ISSUE_B60: Ready
# ISSUE_B61: Ready
# ISSUE_B62: Backlog   (blocked by ISSUE_B130)
# ISSUE_B63: Ready
# ISSUE_B64: Ready
# ISSUE_B130: Backlog   (blocked by ISSUE_B55)
# ISSUE_B134: Ready
# ISSUE_B128: Ready
# ISSUE_B65: Backlog   (blocked by ISSUE_B128)
# ISSUE_B132: Backlog   (blocked by ISSUE_B128, ISSUE_B65)
# ISSUE_B133: Backlog   (blocked by ISSUE_B128)
# ISSUE_B66: Backlog   (blocked by ISSUE_B132)
# ISSUE_B67: Backlog   (blocked by ISSUE_B66, ISSUE_B132)
# ISSUE_B68: Backlog   (blocked by ISSUE_B65, ISSUE_B130)
# ISSUE_B69: Backlog   (blocked by ISSUE_B130)
# ISSUE_B70: Backlog   (blocked by ISSUE_B132)
# ISSUE_B71: Backlog   (blocked by ISSUE_B65)
# ISSUE_B73: Backlog   (blocked by ISSUE_B133)
# ISSUE_B74: Backlog   (blocked by ISSUE_B133)
# ISSUE_B77: Ready
# ISSUE_B78: Ready

echo "Created:"
echo "  B55 -> #$ISSUE_B55"
echo "  B56 -> #$ISSUE_B56"
echo "  B57 -> #$ISSUE_B57"
echo "  B58 -> #$ISSUE_B58"
echo "  B59 -> #$ISSUE_B59"
echo "  B60 -> #$ISSUE_B60"
echo "  B61 -> #$ISSUE_B61"
echo "  B62 -> #$ISSUE_B62"
echo "  B63 -> #$ISSUE_B63"
echo "  B64 -> #$ISSUE_B64"
echo "  B130 -> #$ISSUE_B130"
echo "  B134 -> #$ISSUE_B134"
echo "  B128 -> #$ISSUE_B128"
echo "  B65 -> #$ISSUE_B65"
echo "  B132 -> #$ISSUE_B132"
echo "  B133 -> #$ISSUE_B133"
echo "  B66 -> #$ISSUE_B66"
echo "  B67 -> #$ISSUE_B67"
echo "  B68 -> #$ISSUE_B68"
echo "  B69 -> #$ISSUE_B69"
echo "  B70 -> #$ISSUE_B70"
echo "  B71 -> #$ISSUE_B71"
echo "  B73 -> #$ISSUE_B73"
echo "  B74 -> #$ISSUE_B74"
echo "  B77 -> #$ISSUE_B77"
echo "  B78 -> #$ISSUE_B78"
