---
name: next-issue
description: Refresh the Karetao board from the issue dependency graph and say what is Ready, with the background Lenton needs to choose.
disable-model-invocation: true
---

Lenton is choosing what to work on next. He learns the project by working it, so each Ready issue
gets a short background, and the board must already show the true picture when he opens it.

## Steps

1. **Refresh the board.** Run `python3 -I icm-project/tools/issue_graph/issue_graph.py --apply`.
   If it exits asking for the project scope, run it again without `--apply` and carry the exact
   scope instruction it printed into your reply; the plan is still correct, only the board write
   is skipped. Done when the plan has printed and either the board is updated or the reason it
   was not is in hand.
2. **Background each Ready issue.** For every issue the plan lists under "Ready now", read the
   issue (`gh issue view <n> --comments`) and the documents its body cites, then write one
   paragraph: what the issue changes, which requirement or ruling it serves (cite the file and
   row), what it unblocks (from the plan's "blocks" count and the graph), and the one concept he
   will meet doing it (name it so he can look it up). Done when every Ready issue has its
   paragraph and no paragraph repeats the issue title as its content.
3. **Recommend one.** Pick the issue that unblocks the most others; break ties toward the lowest
   stage. Say why in one sentence, and name the command to start it: `/work-issue <n>`.

## Reply shape

Milestone, then the Ready issues as a list with their paragraphs, then the recommendation, then
the board status line (updated, or the scope instruction). Blocked and Backlog issues appear only
as a count per milestone unless he asks.
