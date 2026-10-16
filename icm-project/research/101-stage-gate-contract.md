# Issue #101: Update the issue contract with the stage-gate rule from the Wayfinder map

Date: 2026-10-16. Branch: `issue/101-stage-gate-contract`. Requirement or ruling served: the strict stage gate decided in #95 (points 1 to 3 and 5) and the bench bring-up slot decided in #98, both on Wayfinder map #94. A process rule, so it lives in `.github/ISSUE_CONTRACT.md` and the `issue_graph` card, not in `Documentation/`.

## Predictions

A process-only issue: the rulings were Lenton's own (#95, #98), so the ruling and contract layers were explained, and predictions were asked on the code only. No hardware layer.

| Layer | Question | Lenton's prediction | What the source showed | Pointer |
|---|---|---|---|---|
| Ruling | (explained) A stage closes before the next opens; membership is a dependency claim backed by an edge; no milestone is non-stage work, bench bring-up named. | n/a | #98 calls the bench the one exception to membership by edge: #108 blocks #67 with no milestone. | #95, #98 resolutions |
| Contract | (explained) Where does an agent read the gate today? | n/a | Nowhere in the contract: "Milestones" said only that milestones are stages, not dates. The rule lived in the tool card and the #95 comment. | `.github/ISSUE_CONTRACT.md:116-118` |
| Code | How does an issue with no milestone affect the current stage, and what Status does it get unblocked? | Counts as Stage 0; Ready | Half held. Ready, yes; but it is filtered out before the lowest stage is taken, so it never holds a gate. `stage_key(None)` = `(1, 0)` only sorts it last on the board. | `issue_graph.py:91`, `:96`, `:80-87` |
| Code | X in Stage 2 blocks Y in Stage 1; what happens? | Lenton: "a question incorrectly framed as a prediction" (the options read as design choices) | Fixed by the code: Y `Blocked`, X `Backlog`, Stage 1 never closes, so Stage 2 never opens: a circular wait. Nothing warns. The "lowest stage" placement rule is what prevents it. | `issue_graph.py:94-95`, `:98` |

## Decisions

| Question | Decision | Why |
|---|---|---|
| Membership wording | Add the deliverable clause, then (second review) make it the lower of two stages: the stage whose goal it delivers, and the lowest stage holding an issue it blocks; enabling work that blocks nothing is closed as not planned. | Read alone, "the lowest stage holding an issue it blocks" gives no stage to the ten staged issues that block nothing (#67, #85 to #91, #45, #13). #95 wrote the rule for chores. A deliverable placed only by its goal could still block an earlier stage's issue and deadlock; taking the lower stage rules that out. The live graph had no such inversion when this was written. |
| Sentence count | Three sentences instead of the issue's two. | The deliverable clause made the membership sentence too long to read in one go. |
| Bench wording | "its phases block staged issues (#108 blocks #67)", not only "its last phase blocks #67". | Since #97 the bench edges are #105 → #83, #107 → #91 and #108 → #67. |
| How the current stage is named | "the lowest `Stage N` by the number in the milestone title (not GitHub's milestone number)", in the contract and the card's Ready rule. | GitHub numbers milestones by creation: #1 is Stage 3, #8 Stage 1, #10 Stage 0. `stage_key()` parses the title (`issue_graph.py:80-87`), so "lowest-numbered milestone" misdescribed the code. Found by the review. |
| One list of no-milestone work | The Milestones paragraph holds it; the Order paragraph (#97) and the card point to it. | The Order paragraph listed "bench bring-up phases, decision tickets, maps", the new text "planning tickets and bench bring-up": two lists to keep in step. Found by the review. |

## Concepts met

- **Stage gate (phase gate)**: a milestone that must close before the next one opens; `issue_graph` makes only the lowest open milestone current, so Ready follows it.
- **Membership by edge**: a stage placement is a claim that something in that stage needs the issue; a native GitHub dependency is the evidence for the claim.
- **Circular wait (deadlock)**: a blocker placed in a later stage than its dependent waits for a stage that cannot open until the dependent closes. Prevented by the placement rule, not detected by the tool.
- **Surrogate key versus natural key**: GitHub's milestone number is a surrogate key (assigned in creation order, meaning nothing); the `Stage N` in the title is the natural key the gate orders by. Text that names the one while the code uses the other misleads.
- **Single source of truth with a back-reference**: the contract states the rule; the tool card points to it rather than restating it as its own.

## What the change did and how it was verified

`.github/ISSUE_CONTRACT.md` "Milestones" gained a paragraph: the gate, with the current stage defined by the `Stage N` title number; membership (deliverable stage, or the lowest blocked stage for enabling work, closed as not planned if it blocks nothing); and the reserved no-milestone slot (planning tickets, bench bring-up #103 to #108), with the bench as the one exception to membership by edge. Its stage list now names Stage 0 Foundation, and the Order paragraph points to Milestones for what has no milestone. `icm-project/tools/issue_graph/issue_graph.md` RULES gained one line pointing at that section as the source, and its Ready rule names the stage by title. No code changed.

Checks: `doc_check` clean (exit 0), run three times, though it does not scan `.github/` or `icm-project/` (`doc_check.py:42-45`), so its `TERMS` pattern was applied to every added line and this note: no hits. `issue_graph.py` dry run unchanged (no code changed; Ready now #93, #79, #73, #103, #94, #100, #101), and a scan of its `--json` found no staged blocker in a later stage than the issue it blocks, so the new membership rule makes no open issue non-compliant. `/code-review` (medium) twice. The first found nine, all fixed: the current stage named by GitHub's milestone number (it is assigned by creation, #1 is Stage 3) instead of the `Stage N` title; the "blocks nothing" condition dropped; closed #98 listed as no-milestone work; Stage 0 missing from the stage list; two lists of no-milestone work (Order and Milestones); stale line pointers in this note (taken before #97 shifted the file by nine lines); this placeholder; the card's Ready rule with the same numbering ambiguity; and restated rules. The second found nine: four fixed (the deliverable-before-earlier-stage deadlock, Stage 0 phrasing and the titles' em dash, the hardcoded bench range, this placeholder); three recorded below as outside #101's scope; and #9 needed no change, because "Milestones" is a subsection of "Karetao Engineering Project Fields" (`ISSUE_CONTRACT.md:100`, `:116`), so the card cites one section, and the card's Order bullet describes the code, which is its job. No build or tests apply.

## Open questions

- A stage-inversion warning in `issue_graph.compute()` (a blocker in a later stage than the issue it blocks), about five lines; a follow-up to ticket or drop. Not built here: #101 is "No code change".
- Non-stage milestones: the section's opening sentence still allows "release groupings", and `stage_key()` gives any milestone not titled `Stage N` the key `(0, 99)`, so it would become current once the stages close (`issue_graph.py:80-87`, `:91`). None is open today (M3 to M7 closed). Either drop "release groupings" or make the tool ignore non-stage milestones; a decision for Lenton.
- Enabling work that blocks only no-milestone issues (a tool the bench needs) has no placement rule; #95 did not decide it. Plausibly it is non-stage work itself.
- #110 (BenchWork notebook prototype) has no milestone but is neither a planning ticket nor bench bring-up, so it does not fit the slot as now written. Its placement belongs to another issue.
