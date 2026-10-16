# Issue #97: Decide the Stage 1 walking order among unblocked siblings

Date: 2026-10-16. Branch: `issue/97-stage1-walking-order`. Ruling served: map #94 (route to Stage 1 verified); #95 (strict stage gate, membership by edge), #98 (bench tracking), #99 (working rhythm).

Decision issue: no predictions. When #97 was written #80 was still open; it merged (PR #114) before this session, so the "first Stage 1 issue" question became #81 or #83.

## Mechanism

| Layer | What the source shows | Pointer |
|---|---|---|
| Ruling | #95: a stage opens only when the one before is empty; an issue sits in a stage through a native edge, and a chore that blocks nothing is closed. #98: bench phases #103 to #108 carry no milestone (always Ready) and were to go "first in the manual order". #99: one issue in flight at a time, so "walking order" means the sequence `/next-issue` recommends. | map #94 "Decisions so far" |
| Contract | "The board's manual item order within a milestone is the priority." | `.github/ISSUE_CONTRACT.md` §Order (before this change) |
| Code | `--apply` re-places every board item on each run (`updateProjectV2ItemPosition`), sorted by stage, then GitHub's direct `blocking` count, then number; no-milestone issues sort last. `/work-issue` runs `--apply` after every merge, so a hand order lasts until the next merge, and #98's "bench first" was already overwritten. `/next-issue` step 4 ignored the board order and picked by blocking count. | `icm-project/tools/issue_graph/issue_graph.py` `compute()`, `stage_key()`, board step 3; `.claude/skills/next-issue/SKILL.md` step 4 |
| Graph | Hidden dependencies in the Stage 1 siblings: #67 runs "per `ENCODER_BENCH_PROCEDURE`", which #92 extends to SYS-ENC-002 (no edge); #105 sets the sensor rail and I2C levels #83 relies on (no edge); #83's acceptance criteria re-measured PRM-ACQ-02 "with the sweep counter" that #91 builds, while #91 is blocked by #83 (unclosable); #78 grows `ExchangeSession` from `TimingSession` keeping `TransactionRecord`'s CSV fields, including the three dead fields #93 deletes (ruling R7). | issue bodies #67, #83, #91, #92, #93, #105, #78; `RaspberryPi_Sensor_Hub/src/spi/timing.py:83-100` |
| Tie-break | GitHub's `issue_dependencies_summary.blocking` counts direct dependents only: #73, #78, #79 and #93 all showed "blocks 1", so the number put #73 first although #93 heads the chain #93 → #78 → #102 → (#75, #86, #87, #42 ...). | dry run before the tie-break change |

## Decisions

| Question | Decision | Why |
|---|---|---|
| Where does the order live? | The graph is the order. `issue_graph` computes the board order and nobody sets it by hand; a deliberate sequence is a native edge with its reason in the later issue; a preference with no reason is left to the tie-break. Contract §Order and rule 5 rewritten. | One source; `--apply` would wipe any other; #95 and #99 already made the graph the plan. |
| Bench and stage work | Bench last, picked by hand. No-milestone issues (bench phases, decision tickets, maps) stay after the stages in the order; `/next-issue` recommends the first Ready milestone issue and lists the Ready bench phases for Lenton to pick when he is at the bench. Supersedes #98's "first in the manual order". | A bench phase needs Lenton at the bench; the code track should not stall when he is not. |
| First Stage 1 issue | #81 (GET_SNAPSHOT). | Head of the critical path #81 → #82 → #66 → #67; builds on #80's snapshot path. No edge needed. |
| #105 and #83 | Edge: #105 blocks #83. | Phase 2's measured rail and pull-ups feed #83's I2C work; only an edge survives `--apply`. |
| #83's re-measure criterion | Moved to #91; edge #107 blocks #91. | #91 builds the sweep counter; the re-measure needs the encoders read over SWD (bench phase 4). #83 can now close. |
| #92 | Edge: #92 blocks #67. | #67 follows the procedure #92 completes; keeps #92 in Stage 1 by #95's rule. |
| #93 | Edge: #93 blocks #78; milestone moved to Stage 0. | Deleting the dead fields before #78 copies `TransactionRecord` changes the CSV columns once; ruling R7 stays applied. |
| Tie-break | Sort by stage, then the number of open issues downstream (transitive), then number. The `Blocking` board field stays the direct count. | Direct fan-out ranked #73 above #93; the downstream count follows the longest chains. |

Resulting order (dry run 2026-10-16): Stage 0 #93, #78, #102, #79, #73; Stage 1 #81, #82, #66, #83, #75, #84, #92, then the leaves by number; bench #103 to #108 after the stages.

## Concepts met

- **Topological order with a tie-break**: the dependency graph is a partial order (a DAG); any total order that respects it is valid, so the only real choice is the tie-break and where it lives.
- **Out-degree versus transitive closure**: GitHub's `blocking` is the out-degree (direct dependents); the new sort counts every descendant, a cheap stand-in for critical-path scheduling. `compute()` inverts the fetched `blocked_by` lists and walks them with a stack.
- **Derived state versus hand state**: a value a tool recomputes on every run (board order) cannot also be hand-maintained; either the tool owns it or it reads it. Status splits the same way (`Blocked/Ready/Backlog` derived, `In Progress/Verification/Done` by hand).

## What the change did and how it was verified

The decisions are applied in two places. On GitHub (2026-10-16): four native edges (#105→#83, #107→#91, #92→#67, #93→#78), #93 moved to Stage 0, #83's PRM-ACQ-02 re-measure criterion moved to #91, the resolution comment on #97 and the map #94 Decisions line. In the repo: `issue_graph.py` `compute()` inverts the fetched `blocked_by` lists into a dependents map and counts each issue's reachable descendants (a stack walk with a seen set, so a cycle terminates), and sorts by stage, then that count, then number; the plan prints it as `down`, `--json` as `downstream`; `open_issues` now pages the REST listing by hand. `ISSUE_CONTRACT.md` (rule 5, Order), `ISSUE_FRAMEWORK.md` §7.2, the tool card and `/next-issue` steps 3 and 4 say the order is computed from the graph and never set by hand.

Checks: `doc_check` clean; `py_compile` of the tool; a dry run printing the order above (44 issues, the same set as before the change); `--json` carries `downstream`; `compute()` exercised on a synthetic graph (chain, cross-stage dependent, no-milestone blocker, a two-issue cycle) with the expected order and counts. No firmware or Pi code changed, so no build or test suite applies. `/code-review` (medium) raised eight findings, all fixed: `ISSUE_FRAMEWORK.md` §7.2 still said manual order; `/next-issue` had no pick when only a bench phase is Ready (fallback added); docs now say a no-milestone blocker sorts after the staged issue it blocks and the Blocked status carries the edge (Lenton's "bench last"); the listing was one page of 100 including PRs (now paged, since a dropped issue would cut every downstream count through it); "every item" corrected to "every open issue" and rule 5 limited to the derived Statuses; step 3 cites the `down` count; cross-stage descendants documented as counted on purpose; card line wrapping.

## Open questions

- The `Blocking` board field and the Chokepoints view still show the direct count; switch them to the downstream count if the two numbers confuse.
