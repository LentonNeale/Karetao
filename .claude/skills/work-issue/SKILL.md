---
name: work-issue
description: Work one Karetao GitHub issue in learning mode, then run the story loop to a held, reviewed change.
disable-model-invocation: true
---

Argument: the issue number. Lenton builds Karetao to understand embedded firmware, electronics,
robotics and engineering process, so this skill runs **prediction first**: before showing how a
mechanism works, ask him to predict it, then show the code or datasheet and compare. One question
per AskUserQuestion call, recommended option first.

The authority order never changes: `Documentation/**` over component docs over code over the
issue text. An issue that contradicts a document is wrong; say so and follow the document.

## Steps

1. **Take the issue.** Read it with comments. Set its board Status:
   `python3 -I icm-project/tools/issue_graph/issue_graph.py --set-status <n> "In Progress"`
   (if that fails for scope, say so once and continue). If the issue has open blockers (the issue
   page's Blocked by list, or `--json` from the same tool), stop and report them: the graph is the
   plan. Done when the issue, its blockers and the documents it cites are in context.
2. **Orient, prediction first.** Walk the mechanism the issue touches, in this order and no further:
   the system requirement or ruling it serves; the interface or configuration contract; the code
   path (name file and line); the hardware fact behind it (register, timing, electrical, from the
   reference notes). For each layer, ask one prediction question, then show the source and state
   whether his prediction held and why. Read only the reference rows `icm-project/references/ROUTING.md`
   names for the code areas touched. Done when every layer has one prediction recorded and he has
   said he is ready to plan. Three or more layers is normal; fewer only when the issue is
   documentation-only.
3. **Write the note.** Create `icm-project/research/<n>-<slug>.md` from [`note-template.md`](note-template.md):
   predictions and outcomes, the concepts met, the pointers. Keep adding to it through step 5.
4. **Plan the change.** List the files, the tests, the documents that must change in lockstep
   (SPI protocol: C and Python together; `.ioc` edits regenerate `Core/` headless), and the
   verification commands that apply. Ask him to confirm the plan in one question.
5. **Story loop.** In a worktree (`EnterWorktree`, name `issue-<n>`), branch `issue/<n>-<slug>`:
   implement; run every applicable verify command from the project `CLAUDE.md` Commands section
   (Debug build for firmware, HostTests, Pi tests, `doc_check`; Release when firmware changed);
   run `/code-review` on the branch and fix every finding; rerun the checks. Done when all checks
   pass and the review has no open finding.
6. **Hold.** Set Status `Verification`. Show him the diff summary, the check results, and the note.
   Commit only on his word; the message cites `#<n>`; closing the issue is his call, ask once.
   Done when he has said commit, change, or stop, and the note's final section is filled.

## Boundaries

- Numbers come from `PARAMETER_REGISTER.md` with a basis; a new value needs a row and "Provisional"
  is the word for an estimate.
- Decisions go in `Documentation/07_DECISIONS/`, never in the issue body; propose, he decides.
- CubeMX output is regenerated from the `.ioc`, never edited by hand.
