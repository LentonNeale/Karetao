#!/usr/bin/env bash
# Ask the subject-expert (Haiku, read-only) each question in icm-project/tests/experts/<subject>.md
# and check the answer text, the Basis label and that a path:line source is cited.
# Usage: tests/experts/run.sh [subject]
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
ws="$(cd "$here/../.." && pwd)"; root="$(cd "$ws/.." && pwd)"
res="$here/results"; mkdir -p "$res"
pass=0 fail=0 cost=0

for qf in "$root"/icm-project/tests/experts/*.md; do
  subject=$(basename "$qf" .md)
  [ -n "${1:-}" ] && [ "$subject" != "$1" ] && continue
  n=0
  while IFS=$'\t' read -r q expect basis; do
    n=$((n+1)); out="$res/$subject-$n.json"
    (cd "$root" && timeout 300 claude -p "Subject: $subject
Question: $q" --agent subject-expert --model haiku --output-format json \
      --disallowedTools Bash Write Edit NotebookEdit WebFetch WebSearch Agent < /dev/null > "$out" 2>/dev/null)
    ans=$(jq -r '.result // ""' "$out" 2>/dev/null); c=$(jq -r '.total_cost_usd // 0' "$out" 2>/dev/null)
    cost=$(awk -v a="$cost" -v b="$c" 'BEGIN{print a+b}')
    printf '%s\n' "$ans" > "$res/$subject-$n.txt"
    errs=()
    grep -qiE -- "($(sed 's/[.[\*^$()+?{}]/\\&/g' <<<"$expect"))" <<<"$ans" || errs+=("answer lacks [$expect]")
    bl=$(grep -i -m1 'basis' <<<"$ans")
    grep -qiE -- "($basis)" <<<"$bl" || errs+=("basis '${bl:-missing}' not in [$basis]")
    [ "$basis" = "not documented" ] || grep -qE '[A-Za-z0-9_./-]+\.[a-z]+:[0-9]+' <<<"$ans" || errs+=("no path:line source")
    if [ ${#errs[@]} -eq 0 ]; then echo "PASS  $subject#$n  $q"; pass=$((pass+1))
    else echo "FAIL  $subject#$n  $q"; printf '        %s\n' "${errs[@]}"; fail=$((fail+1)); fi
  done < <(awk '/^## /{if(q)print q"\t"e"\t"b; q=substr($0,4); e=""; b=""}
                /^expect:/{e=substr($0,9)} /^basis:/{b=substr($0,8)}
                END{if(q)print q"\t"e"\t"b}' "$qf")
done
printf -- '---\n%d passed, %d failed. Haiku cost $%.4f. Answers: %s/\n' "$pass" "$fail" "$cost" "${res#$ws/}"
[ $fail -eq 0 ]
