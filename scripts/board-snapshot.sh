#!/usr/bin/env bash
# Markdown table of project-board items: issue, state, Status, Workstream, Work Type, Priority, milestone, title.
# Usage: board-snapshot.sh [--all]   (default: open issues only)
set -euo pipefail
. "$(dirname "$0")/_env.sh"

open=$(gh issue list -R "$GH_REPO" --state open --limit 1000 --json number --jq '[.[].number]')
gh project item-list "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --limit 500 --format json |
jq -r --arg all "${1:-}" --argjson open "$open" '
  .items
  | map(select(.content.type == "Issue"))
  | map(select($all == "--all" or (.content.number as $n | $open | index($n))))
  | sort_by(.content.number)
  | (["#","Status","Workstream","Work Type","Priority","Milestone","Title"] | "| " + join(" | ") + " |"),
    "|---|---|---|---|---|---|---|",
    (.[] | "| \(.content.number) | \(.status // "-") | \(.workstream // "-") | \(.["work Type"] // "-") | \(.priority // "-") | \(.milestone.title // "-") | \(.title) |")'
