# issue_graph

PURPOSE: Show the open issues of `LentonNeale/Karetao` with their native GitHub dependencies, the
board Status each implies, and the order the board should hold; optionally write both to the
Karetao Engineering Project board (project 4).

INPUTS: GitHub, through `gh` (read: `repo` scope; `--apply` and `--set-status`: `project` scope and
AIKaretao as a board collaborator). No files.

OUTPUTS: a plan on stdout (per milestone: number, computed Status, how many issues it blocks
directly, how many lie downstream of it, its open blockers, title; then "Ready now"); `--json` the
same as JSON; `--board` the board changes as a dry run; `--apply` writes them; `--set-status N
STATUS` sets one Status by hand.

RULES (from `.github/ISSUE_CONTRACT.md`, "Karetao Engineering Project Fields"):
- Status `Blocked`: the issue has at least one open blocker (`issue_dependencies_summary.blocked_by`).
- Status `Ready`: no open blocker, and the issue is in the current stage (the lowest-numbered
  milestone with open issues) or has no milestone.
- Status `Backlog`: no open blocker, but a later stage.
- `In Progress`, `Verification`, `Done` are set by people (or GitHub's auto-close workflow) and are
  never overwritten by `--apply`.
- Order: by stage, then the issue with the most open issues downstream first (every issue it holds
  up through the edges, in any stage, not only its direct dependents), then by number;
  no-milestone issues last, even when they block a staged issue (its Blocked status shows the
  edge). This order is the priority and is never set by hand: `--apply` re-places every open
  issue. A deliberate sequence within a stage is a native edge with its reason in the issue (#97).
- `Blocking` (Number field, tool-owned): the count of open issues this one blocks, written on every
  `--apply`; the Chokepoints view sorts on it. Never edit it by hand.

PSEUDO CODE:
  issues = open issues (REST, PRs dropped); for each with blocked_by > 0, fetch its open blockers
  current = lowest stage among milestones with open issues
  status(i) = Blocked | Ready | Backlog per the rules; downstream(i) = issues reachable through the
  inverted blocked_by lists; sort by (stage, -downstream, number)
  print; if --board/--apply: load project 4 (GraphQL), add missing items, set computed statuses
  where the current value is not a human one, then re-place every item in the sorted order.

Run: `python3 -I icm-project/tools/issue_graph/issue_graph.py [--board | --apply | --json]`
     `python3 -I icm-project/tools/issue_graph/issue_graph.py --set-status 42 "In Progress"`
