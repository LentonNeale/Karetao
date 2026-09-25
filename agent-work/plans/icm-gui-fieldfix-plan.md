```
issue: none yet
task: icm-gui-fieldfix
stage: 04-implement
status: draft
author: agent:orchestrator/opus
```

# icm-gui-fieldfix — Subagent plan: make the GUI usable on Karetao (revision 2)

> **Home of this plan:** `agent-work/plans/` on branch `agent-work/icm-gui`. Copies elsewhere are stale.

**Inputs:**
- the Karetao field report (`field-feedback/karetao`: `feedback/karetao/icm-gui-field-feedback.md`, never merged);
- the Karetao orchestrator's handoff note (2026-09-25);
- the User's decisions on F1, F2, F5 and undoing approvals.

**Branch:** `icm-gui-prototype`. **Suggested tier:** T3. Contract edits (C4-like) and the final acceptance block.

## Already done (no work needed)

| Handoff item | State |
|---|---|
| 1. Draft PRs #1 (F3), #2 (F4), #3 (F6) | Merged unchanged into `icm-gui-prototype` (eabb9e1), plus follow-up 4a0d7d8: an unknown Helper task ID now returns an error instead of a traceback |
| 5. Subtree `--rejoin` note | In `gui/INTEGRATION.md` §2 (0cff395) |
| 4. Probe: `--permission-prompt-tool stdio` | Recorded in `icm-gui-chat-plan.md`. The rest of item 4 (headless `liaison.sh`, `permission_denials`) is folded into that plan below; it isn't built in this round. |

## Rules for every subagent in this plan

- **Never edit** `tests/efficiency/**` or `reports/efficiency-tooling/**`. The cloud development agent owns them (its WP1–WP12). If a change seems to need them, stop and report.
- Edit only the files your work package lists under **Owns**. Use the Python standard library only. Don't commit, push or touch GitHub; the orchestrator commits after reviewing.
- Only ever write to temporary copies of the demo data (`gui/fixtures/demo` is read-only).
- **Done** means the WP's check command passes, plus `python3 -m unittest discover -s tests/unit` and `python3 tests/gui/smoke.py`.
- Report: files changed · the check command and its output · anything in this plan that was unclear or impossible (quoted).

**Agents.** `haiku-dev` is this repo's Haiku implementer. `main`'s `python-dev` needs `../icm-project/coding.md`, which this standalone checkout doesn't have, so it isn't used here. Sonnet work packages run as a general-purpose agent on Sonnet with the same rules.

## Waves

| Wave | WPs | Agent | Check |
|---|---|---|---|
| 0 | WP0 merge `main` (a60f2ff) | orchestrator | unit + smoke tests; `git diff` shows no GUI changes from the merge |
| 1 | FF1a workspace contract edits → **CHECKPOINT: the User approves the diff** | orchestrator | liaison tests (4 generic scenarios here) |
| 2 | FF1b author validation + repair · FF5 evidence + `gui.md` config | sonnet · haiku-dev | unit + smoke tests |
| 3 | FF3 multi-role logins | sonnet | unit + smoke tests |
| 4 | FF2 issue import · FF4 undo approval | haiku-dev · haiku-dev | unit + smoke tests |
| 5 | Verification: demo walkthrough, liaison tests, then the Karetao re-test (all 9 liaison scenarios) | build-runner (haiku) · Karetao | see *Verification* |

---

### WP0 — Merge `main` (orchestrator) · 5k

- `git merge origin/main` (a60f2ff). A trial merge shows no conflicts. It brings in:
  - the 11-item Definition of Ready and `## 11. Delivery`;
  - `requester-profile.md`;
  - headless `liaison.sh`;
  - `tests/liaison` with project scenarios and the Delivery check;
  - `tests/efficiency/` and `reports/efficiency-tooling/`.
- Run the unit and smoke tests.
- Add the "never edit `tests/efficiency/**`, `reports/efficiency-tooling/**`" rule to `agents/haiku-dev.md`.
- Commit.

### FF1a — Workspace contracts (orchestrator; User CHECKPOINT) · 15k

Edit **after** WP0, on top of `main`'s versions.

1. **`stages/01-intake/references/brief-template.md`:** the header becomes:
   ```
   issue: none yet
   task: <slug>
   stage: 01-intake
   status: draft
   author: agent:client-liaison/haiku
   tier_suggested:
   tier:
   ```
   The body is unchanged, including `## 11. Delivery`.
2. **`agents/client-liaison.md`**, in "When to write the brief", after "Keep its header block as plain `key: value` lines": set `task:` to the same slug as the file name; keep `author: agent:client-liaison/haiku` exactly; leave `tier_suggested:` and `tier:` empty (the orchestrator and the User set them). Nothing else changes, including the requester-profile rule.
3. **`CONTEXT.md` "Artifact naming":** the header block gains `task: <slug or #NN>` and `author: agent:<name>/<model> | user:<login>`.
4. **`stages/01-intake/CONTEXT.md`, orchestrator step 6:** "Accept the brief (set `status: accepted`)" becomes "suggest a tier (`scripts/review.py … suggest-tier`) and route it; the User selects the tier and approves C1 (in the GUI or with `review.py`)". **This is proposed. If the User prefers to keep `accepted`, the GUI treats `accepted` like `approved` instead (see FF1b).**
5. **`tests/liaison/run.sh`:** for `expect_brief: ready|ready-with-gaps`, also require `^author: agent:client-liaison/haiku$` and a `^task: ` line. The Delivery check and the project-scenario loop stay as they are on `main`.

**Check:** `bash tests/liaison/run.sh`. This uses the real CLI with Haiku, at a few cents per scenario. Only the 4 generic scenarios exist in this checkout; the 5 project scenarios run in Karetao (Wave 5).

### FF1b — Author is mandatory; validation and repair (sonnet) · 100k

**Owns:** `scripts/icmlib.py` (new functions only), `scripts/review.py`, `scripts/stage_status.py`, and a `# --- header validation (FF1b) ---` block in `gui/server.py` and `gui/views.py`, plus tests.

- `icmlib.known_agents(ws_root) -> set[str]`: `agent:<name>/<model>` from the front matter of `agents/*.md`, plus `agent:orchestrator/opus`.
- `icmlib.header_problems(path, header, people, agents) -> list[str]`, which checks for:
  - `author` missing;
  - `author` not a valid identity;
  - a `user:`/`helper:` author not in `people.md`;
  - an `agent:` author not in `agents`;
  - `stage` or `status` missing.
- **`review.py`:**
  - `approve` refuses while there are any problems (`fix the header first: <problems>`).
  - New `set-author <artifact> <identity>`: Users only, and only when `author` is missing or invalid. The identity must pass the same checks. It appends an `author-set` review entry.
  - Treat `status: accepted` as approved everywhere (`awaiting: none`; reopen allowed).
- **`stage_status`:** an artifact with problems gets `awaiting: user`, `blocking: true` and `reason: "invalid header: …"`.
- **`stage_status` (moved here from FF2):** when a task's tier is empty, its brief is `awaiting: user`, `select tier`, even when the brief is approved, so imported work lands in the Queue.
- **Artifact page:** a red banner listing the problems, plus a **Set author** form (a select list of people.md logins and known agents). The form uses the same POST `/action` route (action `set-author`).
- **Tests:**
  - approve is refused without an author;
  - `set-author` by a User succeeds, and by an agent or a Helper is refused;
  - an unknown agent name is refused;
  - an invalid artifact shows up in the Queue as blocking;
  - `accepted` counts as approved;
  - a smoke test for the banner and the form.

### FF5 — Evidence robustness + `icm-project/gui.md` (haiku-dev) · 60k

**Owns:** `icmlib.load_gui_config` (a new function), the `# --- audit/evidence (WP10) ---` blocks, `setup/templates/icm-project/gui.md`, and one line in `setup/questionnaire.md`.

- `load_gui_config(project) -> dict` reads the optional `<project>/gui.md`. It has two sections:
  - `## Acceptance criteria headings`: a bullet list. The defaults are `Acceptance Criteria`, `Completion condition` and `Required outcome`.
  - `## Tier labels`: a table with the columns `| label | tier |`. The default is empty.

  A missing file gives the defaults.
- `/evidence` always returns 200, with one of these explanations:
  - "No spec for this task yet";
  - "No criteria section found (looked for: …)".

  Criteria are found under any configured heading, matched case-insensitively.
- On the Pipeline, the evidence link is greyed out (plain text with a title) when the task has no spec.
- **Tests:** a configured heading ("Completion condition") works, the two explanation pages, and the greyed link.

### FF3 — One login, several roles (sonnet) · 90k

**Owns:** `icmlib.load_people`, the role checks in `review.py`, `helper.py`, `gui/server.py` and `scripts/gui.sh`, `checkpoint_policy.may_approve` (the self-approval comparison only), and tests.

- **`people.md`:** the role cell accepts `user, helper`, and repeated rows are merged. `load_people → dict[str, set[str]]`. Each check becomes `kind in roles`. This replaces `_role_ok` from #2.
- **No-self-approval** compares the *person* for humans: `user:X` can't approve an artifact authored by `helper:X`. Extend the policy truth-table tests.
- **`gui.sh --as <login> [--role user|helper]`:** the default is `user` if the login has it, otherwise `helper`.
- **Server:** the viewer is `(login, acting role)`. The header shows "Acting as User · Switch to Helper" when the login has both roles. Switching is a POST to `/role` that sets an `icm_role` cookie; every request re-validates the cookie against `people.md` and falls back to the default role.
- **Tests:** a two-role login can use both roles, switching changes the tabs, self-approval across roles is refused, and a single-role login is unchanged.

### FF4 — Undo an approval (haiku-dev) · 40k

**Owns:** `cmd_reopen` in `review.py`, the reopen form in `views.py` (the actions block), and tests.

- `reopen <artifact> --text <reason>`: any **User**, on any artifact with status `approved` or `accepted`. The reason is required. It's refused on `applied` with "already applied to GitHub". The review entry is `reopen` with the reason.
- **Artifact page:** Users see a Reopen form with a reason field on approved artifacts. The existing agent-approval Reopen on `/audit` keeps working, but now asks for a reason.
- **Tests:** a User reopens their own approval, a missing reason is refused, `applied` is refused, and the audit reopen passes a reason.

### FF2 — Import from GitHub (haiku-dev) · 80k

**Owns:** `scripts/import_issue.py`, `tests/unit/test_import_issue.py`, `tests/fakes/gh` (a fake `gh`). New files only. **Proposed owner: the local agent**, which has real `gh` access to the project's issues. The "empty tier" rule in `stage_status.py` is moved to FF1b.

Usage:
```
import_issue.py --as user:<login> (<n>... | --all-open) [--dry-run] [--refresh] [--root R] [--project P]
```

- **Read-only.** It uses `gh issue view <n> -R $GH_REPO --json number,title,body,labels,url,state`, and `gh issue list -R $GH_REPO --state open --json number` for `--all-open`. `GH_REPO` comes from `<project>/github.env`. **It never runs a `gh` write command.**
- **Brief stub:** `stages/01-intake/output/<n>-brief.md`. The header is:
  ```
  issue: #n
  task: #n
  stage: 01-intake
  status: approved
  author: user:<login>
  approver: user:<login>
  approved_at: <now>
  tier_suggested: <from gui.md tier labels, or empty>
  tier:
  ```
  The body holds the title, the URL, and "Imported from GitHub; the issue is the source of truth."
- **Spec stub:** `stages/02-issue-spec/output/<n>-spec.md` with `status: applied` and the same author. The body is the title, the URL, and the **criteria section copied from the issue** (found under the `gui.md` headings), under the line "Snapshot of #n at <time>; the issue is authoritative; re-run with --refresh to update".
- **Idempotent:** existing stubs are skipped unless `--refresh` is given, which rewrites only the title and the snapshot. `--dry-run` prints what it would write.
- **`stage_status` rule:** when a task's tier is empty, its brief is `awaiting: user`, `select tier`, **even when the brief is approved**, so imported work lands in the Queue.
- **Tests:** the fake `gh` on PATH returns canned JSON. Cover a dry run, import, skip on re-run, `--refresh`, the tier-label mapping, and a failure that asserts no `gh` write verb is ever called. Also, once FF1b is merged, an imported approved brief with no tier shows "select tier".

---

## Verification (Wave 5)

1. **build-runner (Haiku):**
   - `python3 -m unittest discover -s tests/unit`;
   - `python3 tests/gui/smoke.py`;
   - `scripts/gui.sh --demo-reset --as user1 --check`;
   - `bash tests/liaison/run.sh` (4 generic scenarios; real CLI).
2. **Orchestrator:** updates `tests/gui/walkthrough.md` for Set author, role switching, reopen with a reason, import, and the evidence explanations. Takes screenshots.
3. **Karetao re-test** by the Karetao agent, reported on `field-feedback/karetao` as round 2:
   - `git subtree pull`;
   - **all 9 liaison scenarios pass** (4 generic plus 5 in `icm-project/tests/liaison/scenarios/`), and a fresh liaison brief is approvable in the GUI;
   - `import_issue.py --all-open --dry-run`, then import 3 issues into a copy, select tiers, approve;
   - act as User and as Helper with the same login.

## Folded into the chat-panel plan (next round, not built here)

- The liaison panel runs **`scripts/liaison.sh -p --input-format stream-json --output-format stream-json --verbose --include-partial-messages --permission-prompts host --permission-prompt-tool stdio`**. `liaison.sh` now runs headless without a terminal and passes extra arguments through, so it stays the single source of the liaison's restrictions.
- Both panels answer `control_request`/`can_use_tool`. They also treat any `result` with `permission_denials` > 0 as a warning, even when its subtype is `success`.

## Open (for the User)

- **C2 at T1:** should every spec that becomes a GitHub issue need the User, even at T1? That would be a per-project `user_only_checkpoints: C2` in `gui.md`. Not built until answered.
- **FF1a item 4:** replace the stage 01 status `accepted` with "User approves C1", or keep `accepted` (the GUI supports both)?
- **Next round:** safety-gated Helper tasks, the Helper task field schema, and evidence classes (component, hardware, system).

## Budget

| | Tokens |
|---|---|
| WP0 + FF1a (orchestrator) | 20k |
| FF1b (Sonnet) | 100k |
| FF5 (Haiku) | 60k |
| FF3 (Sonnet) | 90k |
| FF4 (Haiku) | 40k |
| FF2 (Haiku) | 80k |
| Verification (Haiku) | 30k |
| Orchestrator reviews | ~80k |
| **Total** | **≈0.5M** |

Check in at 0.4M. The liaison test runs also use a small amount of real Haiku CLI usage.

## Token log

| WP | Budget | Used | Result |
|---|---|---|---|
