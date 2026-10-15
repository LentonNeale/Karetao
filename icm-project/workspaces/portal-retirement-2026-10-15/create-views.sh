#!/usr/bin/env bash
# Creates the three agreed views on the Karetao Engineering Project board (users/LentonNeale/projects/4).
# Needs gh with the project scope: gh auth refresh -h github.com -s read:project,project
# Run once: bash create-views.sh . Grouping and sorting are finished in the browser (printed at the end).
set -euo pipefail
OWNER=LentonNeale; NUMBER=4

proj=$(gh api graphql -F owner="$OWNER" -F number="$NUMBER" -f query='
query($owner:String!,$number:Int!){ user(login:$owner){ projectV2(number:$number){ id
  fields(first:50){ nodes{ ... on ProjectV2FieldCommon { id name } } }
  views(first:20){ nodes{ name } } } } }')
PID=$(jq -r '.data.user.projectV2.id' <<<"$proj")
[ "$PID" != "null" ] || { echo "project not visible: is the board reopened and this account a collaborator?" >&2; exit 1; }
echo "fields on the board:"; jq -r '.data.user.projectV2.fields.nodes[] | "  " + .name' <<<"$proj"

field_id() { jq -r --arg n "$1" '.data.user.projectV2.fields.nodes[] | select(.name==$n) | .id' <<<"$proj"; }
ids() { for n in "$@"; do id=$(field_id "$n"); if [ -n "$id" ]; then echo "$id"; else echo "  (no field named '$n'; skipped)" >&2; fi; done; }

create() { # name layout filter fieldnames...
  local name=$1 layout=$2 filter=$3; shift 3
  if jq -e --arg n "$name" '.data.user.projectV2.views.nodes[] | select(.name==$n)' <<<"$proj" >/dev/null; then echo "view exists: $name"; return; fi
  local -a visargs=(); local id
  while read -r id; do [ -n "$id" ] && visargs+=(-F "vis[]=$id"); done < <(ids "$@")
  local vid
  vid=$(gh api graphql -F pid="$PID" -F name="$name" -F layout="$layout" "${visargs[@]}" -f query='
    mutation($pid:ID!,$name:String!,$layout:ProjectV2ViewLayout!,$vis:[ID!]){
      createProjectV2View(input:{projectId:$pid,name:$name,layout:$layout,configuration:{visibleFieldIds:$vis}}){ projectV2View{ id } } }' \
    --jq '.data.createProjectV2View.projectV2View.id')
  gh api graphql -F vid="$vid" -F filter="$filter" -f query='
    mutation($vid:ID!,$filter:String!){ updateProjectV2View(input:{viewId:$vid,filter:$filter}){ projectV2View{ id } } }' >/dev/null
  echo "created view: $name ($layout, filter: $filter)"
}

create "Now"         BOARD_LAYOUT "is:open"                 Title Status Milestone Labels
create "By stage"    TABLE_LAYOUT "is:open"                 Title Status Milestone Labels "Blocked by" Blocking
create "Chokepoints" TABLE_LAYOUT "is:open -status:Done"    Title Status Milestone Blocking "Blocked by"

cat <<'TXT'

Finish in the browser (view menu, the small arrow next to each view's name):
  Now:         columns are Status already; set "Slice by" none; keep the board's manual order.
  By stage:    Group by -> Milestone; Sort -> none (keeps the board order the issue_graph tool sets).
  Chokepoints: Sort by -> Blocking, descending. If "Blocking" is not offered as a field, use the
               issue_graph plan instead; GitHub exposes dependency counts to views only where the
               field list above showed them.
TXT
