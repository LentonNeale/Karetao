# ICM GUI prototype — acceptance walkthrough

Run every command from the repository root. The demo uses a shared copy of the demo data at `/tmp/icm-gui-demo`, so the browser and the CLI see the same files, while `gui/fixtures/demo` is never changed. Set a different location with `ICM_GUI_DEMO=/path`.

Before you start, and whenever you want a clean slate:

```bash
scripts/gui.sh --demo-reset --as user1 --check     # recopy the demo data, then check the server starts
D=/tmp/icm-gui-demo
R="python3 scripts/review.py --root $D --project $D/icm-project"
```

## 1. Start the GUI as the User

```bash
scripts/gui.sh --demo --as user1
```

**Expected:** the script prints `Open http://127.0.0.1:8765/`. The page has the tabs Queue · Pipeline · Helper · Audit.

## 2. The Queue

Open http://127.0.0.1:8765/

**Expected:**
- Three red **Blocking** items come first:
  - demo-led's brief, reason "select tier", tier —;
  - demo-docs' spec, T1;
  - demo-hw's plan, T4.
- demo-ui's plan (T3) comes last, with a grey **Non-blocking** badge.
- demo-fw doesn't appear: its plan and evidence are waiting on the orchestrator, not on you.

On the **Pipeline** tab, demo-ui shows "✓ proceed" and demo-hw shows "✗ blocked".

## 3. Select a tier and approve a brief

Click demo-led's brief (`10-demo-led-brief.md`) and scroll to the forms under the text.

1. Before selecting a tier, **Approve** is disabled, with the reason "tier not selected".
2. Click **T2** (marked as suggested) → the page says "Action completed" and the header shows `tier: T2`.
3. **Approve** is now enabled. Click it.

**Expected:** `status: approved`, `approver: user:user1`. At T2 the orchestrator may not approve a brief (C1), so it had to be you.

## 4. Ask a question on a spec, answer it, approve

Open http://127.0.0.1:8765/artifact?path=stages/02-issue-spec/output/12-demo-led-spec.md

1. Type a question in **Ask** and submit it → `status: needs-clarification`. Approve is disabled with the reason "1 open question(s) must be answered first".
2. In a second terminal, answer as the orchestrator:
   ```bash
   $R --as agent:orchestrator/opus answer stages/02-issue-spec/output/12-demo-led-spec.md --text "GPIO 5"
   ```
3. Reload the page → `status: draft`, the answer appears in the thread, and **Approve** is enabled. Click it.

**Expected:** `status: approved`.

## 5. Audit feed and reopen

Open the **Audit** tab.

**Expected:** a row for `11-demo-docs-brief.md`, approved by `agent:orchestrator/opus`, with a **Reopen** button.

Click **Reopen** → the brief's status is `draft`. It's a T1 brief written by a Haiku agent, so it goes back to the **orchestrator's** queue, not yours. Check this with:

```bash
python3 scripts/stage_status.py --root $D --project $D/icm-project --awaiting orchestrator
```

## 6. Orchestrator approvals from the CLI

```bash
$R --as agent:orchestrator/opus approve stages/04-implement/output/14-demo-fw-plan.md   # exit 0: T2 plan (C5) written by haiku
$R --as agent:orchestrator/opus approve stages/02-issue-spec/output/13-demo-docs-spec.md # exit 1: "no self-approval"
$R --as agent:orchestrator/opus approve stages/04-implement/output/15-demo-ui-plan.md    # exit 1: "orchestrator may not approve C5 at T3"
```

Artifact paths are relative to `--root`, so they work from any directory.

## 7. The Helper view

Stop the User server (Ctrl+C), or keep it and use another port:

```bash
scripts/gui.sh --demo --as helper1 --port 8766
```

Open http://127.0.0.1:8766/

**Expected:**
- You land on the **Helper** tab. Helpers only get Helper and Pipeline; Queue and Audit return 403 if typed in.
- The order is H2, H1, H4, H3, H5: High before Medium before Low; blocks-approval first; the T4 task before the T2 task.
- **Start** on H2 → `doing`. **Done** with a result → `done`. **Block** with a reason → `blocked`.
- Artifact pages are read-only for the Helper, with no forms. A hand-made approve is refused:
  ```bash
  curl -si -X POST http://127.0.0.1:8766/action -d action=approve -d path=stages/04-implement/output/16-demo-hw-plan.md | grep -i location
  ```
  The redirect message says `helpers cannot approve`, and the plan stays `draft`.

## 8. Evidence view

On the User's **Pipeline** tab, click **evidence** next to demo-fw, or open http://127.0.0.1:8765/evidence?task=demo-fw

**Expected:**
- AC1 met;
- AC2 needs-hardware;
- AC3 **unmapped** in bold.

Helper task H1 (demo-fw, AC2) starts out blocked. Once a User unblocks it and the Helper marks it done, AC2 also shows the Helper's result.

## 9. Automated tests

```bash
python3 -m unittest discover -s tests/unit   # 130 tests, OK
python3 tests/gui/smoke.py                   # All 18 tests passed
```

The `error: …` lines printed during the unit tests are expected: they come from tests of refusals.
