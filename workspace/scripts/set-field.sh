#!/usr/bin/env bash
# Set a single-select project field on an issue's board item, looking IDs up by name.
# Usage: set-field.sh <issue#> "<Field name>" "<Option name>"
set -euo pipefail
. "$(dirname "$0")/_env.sh"
[ $# -eq 3 ] || { echo "usage: $0 <issue#> <field> <option>" >&2; exit 2; }
issue=$1 field=$2 option=$3

project_id=$(gh project view "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --format json --jq .id)
read -r field_id option_id < <(gh project field-list "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --format json |
  jq -r --arg f "$field" --arg o "$option" '.fields[] | select(.name == $f) | [.id, (.options[]? | select(.name == $o) | .id)] | @tsv')
[ -n "${field_id:-}" ] && [ -n "${option_id:-}" ] || { echo "field '$field' / option '$option' not found" >&2; exit 1; }

item_id=$(gh project item-list "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --limit 500 --format json |
  jq -r --argjson n "$issue" '.items[] | select(.content.number == $n and .content.type == "Issue") | .id')
if [ -z "$item_id" ]; then
  item_id=$(gh project item-add "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --url "https://github.com/$GH_REPO/issues/$issue" --format json --jq .id)
fi

gh project item-edit --project-id "$project_id" --id "$item_id" --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null
echo "#$issue $field = $option"
