# issue_graph

PURPOSE: Show the open issues of `LentonNeale/Karetao` with their native GitHub dependencies, the
board Status each implies, and the order the board should hold; optionally write both to the
Karetao Engineering Project board (project 4).

INPUTS: GitHub, through `gh` (read: `repo` scope; `--apply` and `--set-status`: `project` scope and
AIKaretao as a board collaborator). No files.

OUTPUTS: a plan on stdout (per milestone: number, computed Status, how many issues it blocks, its
open blockers, title; then "Ready now"); `--json` the same as JSON; `--board` the board changes as a
dry run; `--apply` writes them; `--set-status N STATUS` sets one Status by hand.

RULES (from `.github/ISSUE_CONTRACT.md`, "Karetao Engineering Project Fields"):
- Status `Blocked`: the issue has at least one open blocker (`issue_dependencies_summary.blocked_by`).
- Status `Ready`: no open blocker, and the issue is in the current stage (the lowest-numbered
  milestone with open issues) or has no milestone.
- Status `Backlog`: no open blocker, but a later stage.
- `In Progress`, `Verification`, `Done` are set by people (or GitHub's auto-close workflow) and are
  never overwritten by `--apply`.
- Order: by stage, then the issue that blocks the most others first, then by number. The board's
  manual order is the priority; this tool is what sets it.

PSEUDO CODE:
  issues = open issues (REST, PRs dropped); for each with blocked_by > 0, fetch its open blockers
  current = lowest stage among milestones with open issues
  status(i) = Blocked | Ready | Backlog per the rules; sort by (stage, -blocking, number)
  print; if --board/--apply: load project 4 (GraphQL), add missing items, set computed statuses
  where the current value is not a human one, then re-place every item in the sorted order.

Run: `python3 -I icm-project/tools/issue_graph/issue_graph.py [--board | --apply | --json]`
     `python3 -I icm-project/tools/issue_graph/issue_graph.py --set-status 42 "In Progress"`
