# ICM GUI — integration and field-test brief

**Audience:** an Opus agent working in a project that includes this ICM workspace (normally as `workspace/`, a git subtree, next to `icm-project/`).

**Job:**
1. Bring the GUI into that project.
2. Test it against the project's **real** ICM data.
3. Write a feedback report that tells the GUI's maintainer everything needed to make it work for this project.

You are the field tester, not the maintainer:
- **Don't change the GUI code** in the project's `workspace/` copy. When something needs changing, describe the change in the report, or propose it as a draft pull request against the Karetao repo (see section 5).
- Project configuration under `icm-project/` is yours to add, with the User's approval.

---

## 1. What the GUI is

It's a local web front end (http://127.0.0.1:8765, Python standard library only, no JavaScript) for the ICM stage workflow. There are two kinds of human:

- **User:** makes every decision. Selects each task's tier, approves checkpoints, comments, and asks clarifying questions on briefs and specs.
- **Helper:** does physical tasks (tests, hardware set-up, firmware uploads) from a prioritised list and reports results. Never approves or decides.

### Pages

| Page | Who | Shows |
|---|---|---|
| `/` Queue | User | Artifacts waiting on the User. **Blocking** items first (red), **Non-blocking** after them (grey). |
| `/pipeline` | both | Tasks × stages 01–06, with status, tier, "can proceed / blocked", and an evidence link per task |
| `/artifact?path=…` | both (forms for the User only) | The header, the body, and the review thread. Forms: approve, request changes, comment, ask (briefs and specs), tier T1–T4 (briefs), reopen. |
| `/helper` | both (actions for the Helper) | Helper tasks: Start, Done (with a result), Block (with a reason); Unblock (User) |
| `/audit` | User | Approvals made by agents, with Reopen |
| `/evidence?task=…` | both | Acceptance criteria → evidence rows and completed Helper tasks. Criteria with neither are shown **unmapped**. |

### Tiers and who approves

These are set per task, on its brief:

| Tier | Checkpoints required | Approver | Does a pending approval block? |
|---|---|---|---|
| T1 Simple | C1 brief, C2 spec, C7 close-out (+ C3/C4 when present) | The orchestrator for other agents' work; otherwise the User | yes |
| T2 Standard | C1, C2, C5 plan, C6 evidence, C7 | User: C1, C2, C7. Orchestrator: C5, C6 | yes |
| T3 Non-blocking human | all | User | only C2, C3, C4, C7 |
| T4 Blocking human | all | User | all |

These apply at every tier:
- No one approves their own work.
- Helpers never approve.
- C3 (design) and C4 (doc diffs) always need the User.
- The orchestrator may only approve work by a model ranked at or below its own (haiku < sonnet < opus).

### Files it reads and writes

All of these live in the workspace's gitignored `stages/*/output/` folders:

- **Artifact header** (the first fenced block):
  ```
  issue: none yet | #12
  task: <slug>          # optional; if missing, the task is "#<issue>", else the file name minus "-<artifact>.md"
  stage: 02-issue-spec
  status: draft | ready | ready-with-gaps | needs-clarification | changes-requested | approved | applied
  author: agent:<name>/<model> | user:<login>
  approver:
  approved_at:
  tier_suggested:       # briefs only
  tier:                 # briefs only; set by the User in the GUI
  ```
  Files with no header block, such as `board.md`, are ignored.
- **Checkpoint by file-name suffix:** `-brief` C1 · `-spec` C2 · `-design` C3 · `-docdiff` C4 · `-plan` C5 · `-evidence` C6 · `-closeout` C7. Anything else isn't approvable.
- **Review thread:** `<artifact>-review.md`, appended only:
  ```
  ### <UTC time> | <kind> | <identity>
  <text>
  ```
- **Helper tasks:** `stages/05-verify/output/helper-tasks.json`. A future version moves them to GitHub issues in the project repo.
- **People and roles:** `icm-project/people.md`:
  ```
  | login | role |
  |---|---|
  | <gh-login> | user |
  | <gh-login> | helper |
  ```

The GUI **never writes to GitHub**. It only edits artifact headers and appends review and Helper files, always through `scripts/review.py` and `scripts/helper.py`; agents can use the same CLIs.

### Code map

| Path | Role |
|---|---|
| `scripts/icmlib.py` | Headers, review threads, identities, task/tier lookup |
| `scripts/checkpoint_policy.py` | The tier table above (`required`, `blocking`, `may_approve`, `approver_needed`) |
| `scripts/review.py` | CLI: `approve`, `request-changes`, `comment`, `ask`, `answer`, `suggest-tier`, `set-tier`, `reopen` |
| `scripts/helper.py` | CLI + `HelperStore`: `list`, `add`, `start`, `done`, `block`, `unblock` |
| `scripts/stage_status.py` | Per-task pipeline state (`--json`, `--awaiting user\|orchestrator\|agent`) |
| `scripts/gui.sh` | Launcher: `--demo`, `--demo-reset`, `--as <login>`, `--port`, `--check` |
| `gui/server.py`, `gui/views.py`, `gui/static/` | The web server and pages |
| `gui/fixtures/demo/` | Demo data (five tasks across the tiers) |
| `tests/unit/`, `tests/gui/smoke.py`, `tests/gui/walkthrough.md` | Tests and the accepted demo walkthrough |

### Known limitations (don't report these unless they block you)

- **Identity isn't verified.** `--as <login>` is trusted; this is a local prototype.
- **Tasks without a brief can't get a tier.** A legacy issue that has only a spec therefore never enters the Queue and can't be approved in the GUI.
- **No CSRF or origin checks yet.** They're planned together with the chat panels.
- **The audit feed shows absolute paths.** Server stderr capture isn't thread-safe.
- **No chat panels yet.** They're designed, but not built. Section 5 collects what they need.

---

## 2. Install into the project (on a branch; the User approves any push)

1. Read the project's `CLAUDE.md` and follow its rules, including its checkpoints.
2. Find how the workspace was added:
   ```bash
   git log --grep='git-subtree-dir: workspace' -1
   ```
   Note whether `--squash` was used, and the prefix (normally `workspace`).
3. Create a branch, e.g. `icm-gui-field-test`, then pull the GUI:
   ```bash
   git subtree pull --prefix=workspace https://github.com/LentonNeale/Karetao_Consulting icm-gui-prototype [--squash]
   ```
   Use `--squash` only if the original add used it. If there are conflicts, stop and report them; don't resolve them in GUI files.
4. Create `icm-project/people.md` with the User's and the Helper's real GitHub logins. **Ask the User for them.** This is project configuration, so it lives in `icm-project/` and not in the workspace.
5. Check the environment:
   - Python ≥ 3.10;
   - `gh auth status` (only needed for the default login);
   - `python3 -m unittest discover -s tests/unit` and `python3 tests/gui/smoke.py`, run from `workspace/`;
   - `workspace/scripts/gui.sh --demo-reset --as <user-login> --check`. This one fails if your login isn't in the *demo's* `people.md`; in that case use `--as user1`.

## 3. Field tests (record everything in the report)

Keep the evidence you gather in the report: command output, timings and screenshots (headless Chromium or Playwright, if available).

- **T1 — Demo sanity.** Run the smoke tests and `--demo --check`. Optionally skim `tests/gui/walkthrough.md` steps 1–3. It was accepted upstream, so only report differences on this machine.
- **T2 — Live, read-only.**
  1. Run `python3 workspace/scripts/stage_status.py` (live mode: root = `workspace/`, project = `icm-project/`).
  2. Start `workspace/scripts/gui.sh --as <user-login>` and open the Queue, the Pipeline and a few artifacts.
  3. Compare with what you know from the project's board (`scripts/board-snapshot.sh`) and its output folders:
     - Is every in-flight task present, and grouped correctly?
     - Are any artifacts missing, misclassified (wrong checkpoint from the file name), or showing the wrong status?
     - What do the project's real artifact names and headers look like? Give 3–5 anonymised examples.
     - How long does each page take?
- **T3 — Live writes on a copy.** Never write to the real output folders.
  1. Copy the whole workspace directory to a temporary folder and run the server against the copy:
     ```bash
     python3 workspace/gui/server.py --root <copy> --project icm-project --as user:<login>
     ```
  2. On real artifacts in the copy, try: set a tier on a real brief, ask and answer, approve, request changes, reopen.
  3. `diff` each changed file against the original. Anything other than header values changing and review files being appended is a bug.
  4. Try `review.py` as `agent:orchestrator/opus` on a real plan or spec, to see where the tier rules allow or refuse it.
- **T4 — Helper, on the copy.**
  1. Add 3–5 realistic Helper tasks with `workspace/scripts/helper.py --root <copy> --project icm-project --as user:<login> add …`, taken from the project's real hardware or firmware verification needs (stage 05 "needs hardware" items).
  2. Open the GUI as the Helper login.
  3. Is the order right? Are the fields enough for real physical work (e.g. board ID, firmware version, a measurement with units, a photo)? What's missing?
- **T5 — Workflow fit.** Read the project's `icm-project/authority.md`, `github.md` and `build.md` (and `PROJECT.md` if present), then judge:
  - Do the tiers and checkpoint rules fit how this project actually works?
  - Which stage artifacts does it produce that the GUI ignores or misreads?
  - What would the User and the Helper need that isn't here?
  - Which project facts would the GUI need from `icm-project/`, e.g. Helper task fields or which roles may unblock?

## 4. Chat-panel readiness (the next feature)

The next version adds:
- a Client Liaison chat panel (right-hand side);
- an interactive Orchestrator panel (bottom).

Both drive `claude -p --input-format stream-json --output-format stream-json` subprocesses. Please record, on this machine:

1. `claude --version`, `claude auth status` (without the token), and whether `workspace/scripts/liaison.sh` (tmux) works.
2. **Permission-protocol probe.** Run this in a throw-away temporary directory. It costs a few cents on Haiku. It checks whether permission prompts reach the host over stdio:

   ```python
   # probe.py — run: python3 probe.py [stdio]
   import json, os, subprocess, sys, time
   env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_SESSION")}
   cmd = ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
          "--model", "haiku", "--permission-prompts", "host"]
   if sys.argv[1:] == ["stdio"]:
       cmd += ["--permission-prompt-tool", "stdio"]
   p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
   send = lambda o: (p.stdin.write(json.dumps(o) + "\n"), p.stdin.flush())
   send({"type": "user", "message": {"role": "user", "content": "Use the Write tool to create note.txt containing hi, then reply DONE."}})
   with open("events.jsonl", "w") as log:
       for line in p.stdout:
           log.write(line); ev = json.loads(line)
           print(ev.get("type"), ev.get("subtype"), (ev.get("request") or {}).get("subtype"))
           if ev.get("type") == "control_request" and ev.get("request", {}).get("subtype") == "can_use_tool":
               send({"type": "control_response", "response": {"subtype": "success", "request_id": ev["request_id"],
                     "response": {"behavior": "allow", "updatedInput": ev["request"]["input"]}}})
           if ev.get("type") == "result":
               break
   p.stdin.close(); p.terminate()
   print("note.txt exists:", os.path.exists("note.txt"))
   ```

   Run it once without and once with `stdio`. Report:
   - the printed event sequence;
   - whether a `control_request` of subtype `can_use_tool` appeared;
   - whether `note.txt` was created;
   - `events.jsonl`, trimmed, with anything secret-looking removed.

## 5. The feedback report

Write it to `workspace/stages/05-verify/output/icm-gui-field-feedback.md`. That folder is gitignored, so project facts stay out of the shared workspace.

**Delivering it:** if you have push access to `LentonNeale/Karetao_Consulting`, ask the User for approval, then:

- **The report:** push it, alone, to a new branch `field-feedback/<project-slug>` as `feedback/<project-slug>/icm-gui-field-feedback.md`. Branch from `icm-gui-prototype`. This branch is **never merged**, because it holds project facts and the workspace is shared by several projects. Tell the User the branch name; the maintainer reads it from there.
- **Proposed fixes (optional):** for findings where you're confident of a fix, push it to a separate branch `field-fix/<project-slug>-<n>` and open a **draft** pull request into `icm-gui-prototype`. Each pull request should hold one finding, reference the finding number in the report, and add or update a test. Don't merge anything; the maintainer reviews, tests and merges. Fix branches must contain no project facts.

Without push access, give the report file to the User instead, who passes it on.

```markdown
issue: none yet
task: icm-gui-field-test
stage: 05-verify
status: draft
author: agent:field-tester/opus

# ICM GUI field feedback — <project name>

## Environment
- GUI commit tested: <`git log -1 --format=%H` of the subtree pull> · OS · Python · browser · claude version

## Summary
- Works as is: …
- Blocks use in this project: … (the top 3, most severe first)

## Findings
| # | Severity (blocker/major/minor) | Test (T1–T5, §4) | What happened | Expected | Evidence (command/output/screenshot) | Proposed fix (diff if possible) |
|---|---|---|---|---|---|---|

## Real data shape
- Artifact name and header examples (anonymised): …
- Artifacts the GUI ignored or misread: …

## Workflow fit
- Tiers and checkpoints vs this project's authority.md: …
- Helper task fields needed: …
- Config the GUI should read from icm-project/: …

## Chat-panel readiness
- claude version / auth / liaison.sh: …
- Probe without stdio: <event sequence, control_request yes/no, note.txt yes/no>
- Probe with stdio: <same>

## Questions for the maintainer
- …
```

**Rules for the report:**
- Facts only, with evidence for each finding.
- Mark guesses as guesses.
- Include no secrets or tokens, and no personal data beyond the logins the User gave you.
- Don't include the project's proprietary content beyond the minimum needed to show a problem.
