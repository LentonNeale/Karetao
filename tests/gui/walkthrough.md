# ICM GUI Prototype Acceptance Walkthrough

**Date:** 2026-09-25

## Prerequisites

The prototype requires `playwright` for screenshots. If `playwright` is not available, screenshots are skipped.

## Step 1: Start the server with demo data

**Command:**
```bash
scripts/gui.sh --demo --as user1
```

**Expected result:**
The server starts on port 8765. Opening http://127.0.0.1:8765/ shows the Queue tab.

**Queue contents (in order, blocking items first):**
- demo-led's brief (marked **Blocking**), reason "select tier", with T2 suggested
- demo-hw's plan (marked **Blocking**)
- demo-ui's plan (marked **Non-blocking**)

## Step 2: Check the Pipeline view

**Command:**
Navigate to http://127.0.0.1:8765/pipeline

**Expected result:**
A table showing tasks × stages 01–06. demo-ui shows "can proceed"; demo-hw shows "blocked".

**Screenshot:** (if playwright available) Save to `tests/gui/screenshots/pipeline.png`

## Step 3: Set tier on demo-led brief and approve

**Command:**
Open http://127.0.0.1:8765/artifact?path=stages/01-intake/output/11-brief.md

1. Select T2 in the tier selector
2. Click Approve

**Expected result:**
The artifact status changes to approved. The page shows the approval in the review thread.

## Step 4: Ask and answer on demo-led spec

**Command:**
Navigate to http://127.0.0.1:8765/artifact?path=stages/02-issue-spec/output/12-spec.md

1. Click Ask and enter a question
2. In another terminal, run:
   ```bash
   python3 scripts/review.py --root gui/fixtures/demo --project gui/fixtures/demo/icm-project --as agent:orchestrator/opus answer stages/02-issue-spec/output/12-spec.md --text "Answered"
   ```
3. Approve the spec

**Expected result:**
- Status changes to needs-clarification when the question is asked
- Approve button becomes enabled after the answer
- Final status is approved

## Step 5: View and reopen demo-docs approval in audit feed

**Command:**
Navigate to http://127.0.0.1:8765/audit

**Expected result:**
The audit feed shows the orchestrator's approval of demo-docs' brief (13-brief.md).

1. Click Reopen
2. Verify demo-docs' brief is back in the Queue with status draft

## Step 6: Test orchestrator CLI approvals

**Commands:**

Approving demo-fw's plan (T2, C5, haiku work):
```bash
python3 scripts/review.py --root gui/fixtures/demo --project gui/fixtures/demo/icm-project --as agent:orchestrator/opus approve stages/04-implement/output/14-plan.md
```
**Expected result:** Exit code 0 (success)

Approving demo-docs' spec (self-approval attempt):
```bash
python3 scripts/review.py --root gui/fixtures/demo --project gui/fixtures/demo/icm-project --as agent:orchestrator/opus approve stages/02-issue-spec/output/13-spec.md
```
**Expected result:** Exit code 1, stderr: "no self-approval"

Approving demo-ui's plan (T3, C5, not allowed at T3):
```bash
python3 scripts/review.py --root gui/fixtures/demo --project gui/fixtures/demo/icm-project --as agent:orchestrator/opus approve stages/04-implement/output/15-plan.md
```
**Expected result:** Exit code 1, stderr: "orchestrator may not approve C5 at T3"

## Step 7: Helper view

**Command:**
Start the server with helper identity:
```bash
scripts/gui.sh --demo --as helper1
```

**Expected result:**
Only two tabs appear: Helper and Pipeline. No Queue or Artifact actions.

1. Navigate to the Helper tab
2. Verify tasks are sorted by: priority (High/Medium/Low), blocks_approval (true first), created ascending
3. Test buttons: Start, Done (with result textarea and optional path), Block (with reason), Unblock (users only)
4. Verify a POST to `/action` to approve is refused (403)

**Screenshot:** (if playwright available) Save to `tests/gui/screenshots/helper.png`

## Step 8: Evidence view

**Command:**
Navigate to http://127.0.0.1:8765/evidence?task=demo-fw

**Expected result:**
- AC1: met
- AC2: needs-hardware (or met if the Helper task is complete)
- AC3: **unmapped** (displayed in bold)

**Screenshot:** (if playwright available) Save to `tests/gui/screenshots/evidence.png`

## Step 9: Run all tests

**Commands:**

Unit tests:
```bash
python3 -m unittest discover -s tests/unit
```
**Expected result:** All tests pass

GUI smoke test:
```bash
python3 tests/gui/smoke.py
```
**Expected result:** All smoke tests pass

## Notes

- The prototype uses demo data only; no real GitHub writes
- Identity is provided via `--as <login>` and role is looked up in `people.md`
- All CLI commands use standard-library imports only
- HTML output is properly escaped to prevent injection
