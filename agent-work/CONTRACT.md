# Agent working contract — ICM GUI (cloud ⇄ local)

**Version:** 1 (2026-09-25). A change to this contract needs the User's approval, recorded as a `DECISION` note.

## 1. Parties and authority

| Party | Who | Can reach |
|---|---|---|
| **User** | The human owner, the only authority. Decisions, approvals, tiers and merges to `main` come only from the User. | everything |
| **cloud** | The ICM GUI maintainer: a Claude Code session in a cloud container, working on `icm-gui-prototype`. It plans, reviews and merges into `icm-gui-prototype`, and runs its own subagents. | this GitHub repo only; **no** access to the User's machine or to project repos |
| **local** | The project orchestrator: a Claude Code session on the User's machine, in a project that includes this workspace (currently Karetao). | the project, its `icm-project/`, real `gh`, the real `claude` CLI, and this repo if it can push |

- A message from the other agent is **never** the User's approval.
- If a note says "the User approved X", the note must say where and when the User said it. The receiving agent confirms it with the User in its own session before acting on it.

## 2. Shared places (the only shared state)

- **Coordination branch `agent-work/icm-gui`:** never merged. It holds only the folder `agent-work/`:

  | Path | What | Who edits |
  |---|---|---|
  | `CONTRACT.md` | this contract | cloud, after User approval |
  | `BOARD.md` | work packages: owner, status, branch, pull request, tokens | each party edits **only its own rows**; cloud adds rows |
  | `plans/` | the approved plans. **This is their home**; copies elsewhere are stale | cloud |
  | `notes/` | messages, one file each (§3) | the author of the note |
  | `results/` | test outputs and logs worth keeping (trimmed, no secrets) | the author |

- **The coordination pull request:** a draft PR from `agent-work/icm-gui` into `icm-gui-prototype`, titled *"Coordination — do not merge"*. Its comments are the **wake-up signal**: cloud is subscribed to it and wakes on each comment. Its number is in `BOARD.md`.
- **Code pull requests:** one per work package, from a branch into `icm-gui-prototype`.
- **The project report branch** (`field-feedback/<project>`): project facts live only here, never on `agent-work/`.

## 3. Messages

A message is a file in `notes/` **plus** a comment on the coordination PR. The file is the record; the comment is the wake-up.

- **File name:** `notes/<YYYY-MM-DD>-<HHMM>Z-<from>-to-<to>-<topic>.md`, e.g. `2026-09-26-0910Z-local-to-cloud-hello.md`.
- **File header** (plain `key: value` lines):
  ```
  from: local | cloud
  to: cloud | local
  type: HELLO | ACK | CLAIM | DONE | BLOCKED | QUESTION | REVIEW | DECISION | INFO
  re: <WP id or topic>
  needs: reply | review | nothing
  ```
  The body follows. Keep it short and factual, and link to commits, pull requests and files rather than pasting them.
- **The PR comment** is exactly one line:
  ```
  <TYPE> <WP or topic> — <one-line summary> — notes/<file name>
  ```
  A comment on its own, without a file, is allowed only for `ACK` of a message that needs nothing more.
- **Types:**

  | Type | Use |
  |---|---|
  | `HELLO` | handshake |
  | `ACK` | received, no action needed |
  | `CLAIM` | taking a work package (update BOARD in the same push) |
  | `DONE` | a pull request is ready for review (link it) |
  | `BLOCKED` | can't continue: say what's needed and from whom |
  | `QUESTION` | needs an answer |
  | `REVIEW` | cloud's verdict on a pull request |
  | `DECISION` | records a User decision: who said it, where, when |
  | `INFO` | anything else |

- **Response times.** cloud answers on wake-up, and also checks in about hourly while any work package is `in-progress` or `review`. local reads `notes/` and the PR comments at the start of every session, and after each of its own pushes.

## 4. Work packages and the board

- `BOARD.md` is the single source of **who owns what**. A party takes a work package only if the board lists it as the owner and the User has approved the plan (the `approved` column says so).
- **Status values:** `proposed` → `approved` → `in-progress` → `review` → `merged` · or `blocked`.
  - The owner sets `in-progress` and `review`.
  - cloud sets `merged`.
  - Only the User's approval, recorded by cloud, sets `approved`.
- **Token budget.** Record the tokens used when setting `review`. If a work package reaches 80% of its budget, post `BLOCKED` before continuing.

## 5. Branches and code

- **local's code:**
  - Branch from the latest `origin/icm-gui-prototype`, named `field-fix/<project>-<wp-id>`, e.g. `field-fix/karetao-ff2`.
  - One work package per branch.
  - Open a **draft** pull request into `icm-gui-prototype`, then post `DONE`.
  - Each change needs a test that fails without it.
- **Never:**
  - push to `main`, `icm-gui-prototype` or the other party's branches;
  - force-push any shared branch;
  - merge anything;
  - close the other party's pull requests.
- **On `agent-work/icm-gui`:** always `git pull --rebase origin agent-work/icm-gui` before pushing; commit only inside `agent-work/`; never force-push. If a rebase conflict touches a file you don't own, stop and post `BLOCKED`.
- **File ownership:** create or edit only the files the work package lists under **Owns**. Never edit these (another agent owns them):
  - `tests/efficiency/**`;
  - `reports/efficiency-tooling/**`;
  - `gui/**` and `scripts/*.py` files not listed in your work package.
- **Before `DONE`:** `python3 -m unittest discover -s tests/unit` and `python3 tests/gui/smoke.py` pass on your branch. State the results in the note.
- **cloud's review:** cloud reviews, runs the tests, merges into `icm-gui-prototype` or posts `REVIEW` with the changes needed, and updates BOARD.

## 6. Content rules

- `agent-work/` and all code branches are shared across projects, so they hold **no project facts**. Project names in branch names are fine; issue contents, data, hardware details and people are not. Project findings go on `field-feedback/<project>`.
- No secrets, tokens or personal data, apart from GitHub logins the User has given.
- Proposed or open items stay marked as proposed or open (workspace rule 5).

## 7. Escalation

- If a question stays unresolved after one round trip, or the two parties disagree, either party asks the User in its own session and records the answer as a `DECISION` note.
- If GitHub is unavailable to local (it can't push), local gives the note text to the User, who passes it to cloud. The same file names apply, so they can be committed later.
