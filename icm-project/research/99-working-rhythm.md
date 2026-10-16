# Issue #99: Decide the working rhythm around /work-issue and where it is written

Date: 2026-10-16. Branch: `issue/99-working-rhythm`. Requirement or ruling served: Wayfinder map #94 destination ("a written working rhythm for how a session runs around `/work-issue`"); the strict stage gate decided in #95. A process decision, so it lives in `.claude/skills/` and the local `CLAUDE.md`, not in `Documentation/`.

## Mechanism

Decision issue: no predictions (Lenton, 2026-10-16: predictions are for implementation issues). The three layers the rhythm rests on:

| Layer | What the source shows | Pointer |
|---|---|---|
| Ruling | A stage closes before the next opens (#95), so one open Stage 0 issue keeps Stage 1 shut. | #95; map #94 "Decisions so far" |
| Contract | An issue closes when its acceptance criteria are met; a PR body's `Closes #<n>` closes it only when the PR merges into the default branch. A finished branch held unmerged leaves its issue open. | `.github/ISSUE_CONTRACT.md:20` (rule 8); GitHub "Linking a pull request to an issue" |
| Code | `issue_graph` counts a blocker only while its issue state is `open`, and takes the current stage as the lowest milestone that still holds an open issue. Board Status (`Verification`) is never read, so it releases nothing. | `icm-project/tools/issue_graph/issue_graph.py:67`, `:81-88` |

Evidence from the first three issues: #68 landed on main and closed; #70 merged through PR #111 and closed; #77 was held as draft PR #112, so #80 (blocking four others) stayed Blocked. After #70 merged, its worktree and its origin branch were left behind.

## Decisions

| Question | Decision | Why |
|---|---|---|
| Merge cadence | Each held branch merges to main before the next issue starts. | The graph is the plan only if finished work is closed; and stacked branches over the same firmware (#77 then #80) cost rebases. |
| Merge path | A PR per issue with `Closes #<n>`; Claude merges with `gh pr merge --merge` on Lenton's word once CI passes. | CI runs on `pull_request`, so a PR is checked before main; one word covers commit, push and merge. |
| When `/next-issue` runs | Whenever choosing: session start, or straight after a merge. Every merge ends with a board refresh inside `/work-issue`. | A merge changes what is Ready, so a list made before it is stale. |
| Batching | Several issues may share a session, never a branch: own worktree, branch, PR and note each. | Review, note and revert stay one-to-one with the issue; one change request never holds two issues. |
| Ending an issue | Note filled and committed with the change; merge (issue closes, board Done); delete the origin branch; remove the worktree and local branch; refresh the board. Stopped before merge: Status `Verification`, worktree kept, note says what is left. | Keeps origin at `main` plus work in flight, and the board true. |
| Where written | The skills own the steps (`/work-issue` "Rhythm", steps 1, 6 and 7; `/next-issue` step 2); the local `CLAUDE.md` "Working method" carries a short summary and the merge permission. | Skills are versioned but load only when run; `CLAUDE.md` loads every session but is not in git. |

## Concepts met

- **Closing keywords**: `Closes`, `Fixes` or `Resolves #<n>` in a PR body link the PR to the issue and close it on merge into the default branch, not before.
- **Derived state versus recorded state**: `issue_graph` derives Ready and Blocked from issue open/closed state and native dependencies; Status set by hand (`In Progress`, `Verification`) is recorded, not derived, and does not feed the graph.
- **Work in progress limit**: one issue in flight at a time, the Kanban rule that finishing beats starting.
- **Stacked branches**: a branch based on an unmerged branch; it inherits the parent's diff and needs a rebase whenever the parent changes.

## What the change did and how it was verified

`.claude/skills/work-issue/SKILL.md` gained a "Rhythm" section, the no-predictions rule for decision issues, a resume path for a held issue, step 6 (fill the note, commit, push, PR with `Closes #<n>`, wait for CI, merge on his word; "commit but hold" parks the PR) and step 7 (close out). `note-template.md` gained Mechanism and Decisions tables for decision issues. `.claude/skills/next-issue/SKILL.md` refreshes first, then reports held work with its blocks count and recommends merging it before picking. The local `CLAUDE.md` "Working method" summarises the rhythm and carries the merge permission (not in git).

Checks: `doc_check` clean, though it does not scan `.claude/skills/` or `icm-project/research/` (`doc_check.py:42-45`), so these files were also grepped for its forbidden terms (none). `/code-review` (medium) found ten issues, all fixed: a stale `origin/main` before the ancestor check (fetch first); a relative `git worktree add` path that would nest a worktree (absolute path from `--git-common-dir`, checked to resolve to the main checkout's `.claude/worktrees`); a CI race where "no checks yet" read as "path-filtered" (checks must appear when the diff touches a CI path); a resume path that took a ready PR and a worktree for granted (`gh pr ready`, recreate, rerun the checks); a parked PR that would block all work (parked exception); held work reported without its blocks count (refresh first, take it from the plan); a template with no decision variant; the stale "commit on Lenton's word" in `CLAUDE.md`; this section claiming checks before they ran; and over-long lines. A second `/code-review` (medium) found ten more, all fixed: Status was set to In Progress before the blocker check, and `issue_graph --apply` never overwrites a hand-set Status (`issue_graph.py:18`, `:154`), so blockers are checked first; an issue stopped before its PR was invisible (worktrees now count as work in flight); the CI wait had no timeout (five minutes, then check `mergeable` and report); the CI paths were copied by hand (now read from the workflows' `paths:` filters); `EnterWorktree` with a name picks its own branch and base, so step 5 always creates the worktree by absolute path with `--unset-upstream`; the resume path skipped the blocker check; step 7 relied on the board's close workflow to set Done (it now sets Done explicitly); a wrong step pointer in this note; and the template's narrower definition of a decision issue. No build or tests apply: no code changed.

## Open questions

- Applying the rhythm to what is outstanding: merge #77 (PR #112) so #80 becomes Ready; remove the leftover `issue-70` worktree and the stale origin branches. On Lenton's word.
- How the per-issue notes accumulate (an index, a concept list, or nothing) is still "Not yet specified" on map #94.
