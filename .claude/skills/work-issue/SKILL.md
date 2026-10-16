---
name: work-issue
description: Work one Karetao GitHub issue in learning mode, then run the story loop to a reviewed change merged to main.
disable-model-invocation: true
---

Argument: the issue number. Lenton builds Karetao to understand embedded firmware, electronics,
robotics and engineering process, so this skill runs **prediction first**: before showing how a
mechanism works, ask him to predict it, then show the code or datasheet and compare. One question
per AskUserQuestion call, recommended option first. A decision issue (`Type: grilling`, or any
issue that resolves a choice rather than changes code) asks no predictions: explain each layer, then
put each decision to him.

The authority order never changes: `Documentation/**` over component docs over code over the
issue text. An issue that contradicts a document is wrong; say so and follow the document.

## Rhythm (decided in #99)

One issue is in flight at a time. It merges to main before the next one starts, because an issue
closes only when its PR merges (`Closes #<n>`), and `issue_graph` counts a blocker and the current
stage by open issues only, never by board Status: a held branch keeps its dependents Blocked and
the stage open. The one exception is a PR he parks on purpose ("commit but hold"). A session may
work several issues one after another, each with its own worktree, branch, PR and note; issues
never share a branch. Run `/next-issue` whenever choosing what to work on next: at the start of a
session, or straight after a merge to carry on.

## Steps

1. **Take the issue.** Read it with comments. If it has open blockers (the issue page's Blocked by
   list, or `--json` from `issue_graph`), stop and report them, and leave its Status alone: the
   graph is the plan, and `issue_graph --apply` never overwrites a hand-set Status. Find work in
   flight: open `issue/*` PRs (`gh pr list --state open`) and `issue-*` worktrees
   (`git worktree list`). If this issue has one, it was held earlier: resume it (enter its
   worktree, or recreate one from the origin branch as in step 5; rerun step 5 if the note does not
   record its checks and review as passed; then step 6, reusing any PR). If another issue has one
   and it is not a parked PR, stop and report it: the rhythm says finish it first. Then set the
   Status: `python3 -I icm-project/tools/issue_graph/issue_graph.py --set-status <n> "In Progress"`
   (if that fails for scope, say so once and continue). Done when the issue, its blockers and the
   documents it cites are in context.
2. **Orient, prediction first.** Walk the mechanism the issue touches, in this order and no further:
   the system requirement or ruling it serves; the interface or configuration contract; the code
   path (name file and line); the hardware fact behind it (register, timing, electrical, from the
   reference notes). For each layer, ask one prediction question, then show the source and state
   whether his prediction held and why (a decision issue: explain the layer, no question). Read only
   the reference rows `icm-project/references/ROUTING.md` names for the code areas touched. Done
   when every layer is covered and he has said he is ready to plan. Three or more layers is normal;
   fewer only when the issue is documentation-only or process-only.
3. **Write the note.** Create `icm-project/research/<n>-<slug>.md` from [`note-template.md`](note-template.md):
   predictions and outcomes (a decision issue uses the template's Mechanism and Decisions tables
   instead), the concepts met, the pointers. Keep adding to it through step 6.
4. **Plan the change.** List the files, the tests, the documents that must change in lockstep
   (SPI protocol: C and Python together; `.ioc` edits regenerate `Core/` headless), and the
   verification commands that apply. Ask him to confirm the plan in one question.
5. **Story loop.** Create the worktree yourself so the branch name and base are exact
   (`EnterWorktree` with a name picks its own branch and base):
   `git fetch origin main`, then
   `git worktree add -b issue/<n>-<slug> "$(git rev-parse --path-format=absolute --git-common-dir)/../.claude/worktrees/issue-<n>" origin/main`,
   then `git branch --unset-upstream` inside it (so a bare push can never go to main), then
   `EnterWorktree` with that path. Implement; run every applicable verify command from the project
   `CLAUDE.md` Commands section (Debug build for firmware, HostTests, Pi tests, `doc_check`;
   Release when firmware changed); run `/code-review` on the branch and fix every finding; rerun
   the checks; record what ran and its result in the note. Done when all checks pass and the
   review has no open finding.
6. **Hold, then merge on his word.** Set Status `Verification`. Show him the diff summary, the check
   results, and the note. Fill the note's final section before committing, so it lands with the
   change. On his word to merge: commit (the message cites `#<n>`), `git push -u origin
   issue/<n>-<slug>`, and open a ready PR whose body says `Closes #<n>` (an existing PR is reused;
   `gh pr ready <pr>` if it is a draft). Wait for CI: read the `paths:` filters of the
   `pull_request` triggers in `.github/workflows/*.yml`; when the diff matches any, checks must
   run, so wait until `gh pr checks <pr>` lists them, then `gh pr checks <pr> --watch`. If none
   appear within five minutes, check `gh pr view <pr> --json mergeable` (a conflicting PR runs no
   workflows) and report to him rather than merge. Only a diff matching no filter merges with no
   checks. When they pass, `gh pr merge <pr> --merge`, which closes the issue. "Commit but hold"
   stops after the PR is open and parks it: say so in a PR comment. Done when he has said merge,
   hold, change, or stop.
7. **Close out.** After the merge: `git fetch origin main`, then confirm
   `git merge-base --is-ancestor issue/<n>-<slug> origin/main`; `git push origin --delete
   issue/<n>-<slug>`; `ExitWorktree` keep, then from the main checkout
   `git worktree remove .claude/worktrees/issue-<n>` and `git branch -D issue/<n>-<slug>`; set
   Status `Done` with `--set-status <n> Done` (the board's own close workflow may be off, and
   `--apply` reads open issues only); refresh the board with `issue_graph.py --apply`. If he
   carries on, run `/next-issue`. If he stopped before merging, leave Status `Verification` and the
   worktree in place, and end the note with what is left. Done when origin holds no branch for the
   issue, its Status is Done, the board is refreshed, and the session is back in the main checkout
   or in the next issue's worktree.

## Boundaries

- Numbers come from `PARAMETER_REGISTER.md` with a basis; a new value needs a row and "Provisional"
  is the word for an estimate.
- Engineering decisions go in `Documentation/07_DECISIONS/`, never in the issue body; propose, he
  decides. Process decisions (how work runs) go in these skills and the local `CLAUDE.md`.
- CubeMX output is regenerated from the `.ioc`, never edited by hand.
- Merging is done only on his word for that issue; a word for one issue does not carry to the next.
