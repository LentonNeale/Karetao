#!/usr/bin/env bash
# Delegation tests: run each scenario through a headless orchestrator session (the default model)
# and check, from the stream-json event log, which subagents it chose, which model they ran on,
# and what the main session ran itself. Prints a token/cost split by model.
# GitHub write commands are not in the allow-list, so a wrong decision cannot touch the tracker.
# Usage: tests/delegation/run.sh [scenario-name-substring]
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
ws="$(cd "$here/../.." && pwd)"
root="$(cd "$ws/.." && pwd)"
res="$here/results"; mkdir -p "$res"
front() { sed -n '/^---$/,/^---$/p' "$1" | sed -n "s/^$2: *//p"; }
body() { awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$1"; }

allow=(Read Glob Grep Agent "Bash(cd *)" "Bash(cmake *)" "Bash(ctest *)" "Bash(python3 *)"
       "Bash(git log *)" "Bash(ls *)" "Bash(gh issue list *)" "Bash(gh issue view *)"
       "Bash($(basename "$ws")/scripts/board-snapshot.sh*)")

pass=0 fail=0
for f in "$here"/scenarios/*.md; do
  name=$(basename "$f" .md)
  [ -n "${1:-}" ] && [[ $name != *"$1"* ]] && continue
  log="$res/$name.jsonl"
  (cd "$root" && timeout 900 claude -p "$(body "$f")" --output-format stream-json --verbose \
      --allowedTools "${allow[@]}" < /dev/null 2>/dev/null) | grep '^{' > "$log"

  agents=$(jq -r 'select(.type=="assistant" and .parent_tool_use_id==null) | .message.content[]?
                  | select(.type=="tool_use" and (.name=="Agent" or .name=="Task")) | .input.subagent_type' "$log" | sort -u | xargs)
  submodels=$(jq -r 'select(.type=="assistant" and .parent_tool_use_id!=null) | .message.model' "$log" | sort -u | xargs)
  mainbash=$(jq -r 'select(.type=="assistant" and .parent_tool_use_id==null) | .message.content[]?
                  | select(.type=="tool_use" and .name=="Bash") | .input.command' "$log")
  errs=()
  want=$(front "$f" expect_agents)
  if [ "$want" = "none" ]; then [ -n "$agents" ] && errs+=("delegated to [$agents] but should have handled it directly")
  else for a in $want; do [[ " $agents " == *" $a "* ]] || errs+=("did not delegate to $a (used: ${agents:-none})"); done; fi
  for a in $(front "$f" forbid_agents); do [[ " $agents " == *" $a "* ]] && errs+=("must not use $a"); done
  m=$(front "$f" expect_subagent_model)
  if [ -n "$m" ]; then
    [ -z "$submodels" ] && errs+=("no subagent activity")
    for sm in $submodels; do [[ $sm == *"$m"* ]] || errs+=("subagent ran on $sm, expected $m"); done
  fi
  re=$(front "$f" forbid_main_bash)
  if [ -n "$re" ] && [ -n "$mainbash" ]; then
    hit=$(grep -E -- "$re" <<<"$mainbash" | head -1); [ -n "$hit" ] && errs+=("main session ran: $hit")
  fi
  jq -e 'select(.type=="result")' "$log" >/dev/null || errs+=("no result event (timeout or crash)")

  usage=$(jq -r 'select(.type=="result") | .modelUsage | to_entries[]
    | "\(.key)\t\(.value.inputTokens + .value.outputTokens + .value.cacheReadInputTokens + (.value.cacheCreationInputTokens // 0))\t\(.value.costUSD)"' "$log")
  printf '%s\n' "$usage" | sed "s/^/$name\t/" >> "$res/usage.tsv"
  if [ ${#errs[@]} -eq 0 ]; then echo "PASS  $name  agents=[${agents:-none}] submodels=[${submodels:--}]"; pass=$((pass+1))
  else echo "FAIL  $name: $(IFS='; '; echo "${errs[*]}")"; fail=$((fail+1)); fi
  printf '%s\n' "$usage" | awk -F'\t' 'NF==3 {printf "      %-28s %9d tokens  $%.4f\n", $1, $2, $3}'
done

echo "--- tokens by model (this run)"
awk -F'\t' 'NF==4 {t[$2]+=$3; c[$2]+=$4; T+=$3; C+=$4}
  END {for (k in t) printf "  %-28s %9d tokens (%4.1f%%)  $%.4f\n", k, t[k], 100*t[k]/T, c[k]; printf "  total cost $%.4f\n", C}' "$res/usage.tsv"
rm -f "$res/usage.tsv"
echo "$pass passed, $fail failed. Event logs: ${res#$ws/}/"
[ $fail -eq 0 ]
