#!/usr/bin/env bash
# Efficiency test: digest the User's past sessions locally, ask the orchestrator (with its team) for
# tool/hook/shared-file proposals per CONTEXT.md, then validate and rank them.
# Usage: workspace/tests/efficiency/run.sh [--skip-extract] [extra transcript folders...]
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
ws="$(cd "$here/../.." && pwd)"; root="$(cd "$ws/.." && pwd)"
res="$here/results"; mkdir -p "$res"
cd "$root"

if [ "${1:-}" != "--skip-extract" ]; then
  extra=(); for f in "$@"; do extra+=(--transcripts "$f"); done
  default="$HOME/.claude/projects/$(printf '%s' "$root" | sed 's/[^A-Za-z0-9]/-/g')"
  python3 "$here/extract_usage.py" --project-root "$root" --transcripts "$default" "${extra[@]}" --out "$res/digest.json" || exit 1
fi
rm -f "$res/proposals.json" "$res/summary.md"

rel="${here#$root/}"
timeout 1800 claude -p "Run the efficiency test defined in $rel/CONTEXT.md. Follow its Inputs, Process and Outputs exactly, and the delegation policy in workspace/CLAUDE.md. Write $rel/results/proposals.json and $rel/results/summary.md, then run the checker and fix every error it reports." \
  --output-format json --permission-mode acceptEdits \
  --allowedTools Read Glob Grep Write Edit Agent "Bash(python3 *)" "Bash(jq *)" "Bash(ls *)" "Bash(cat *)" "Bash(grep *)" \
  --disallowedTools WebFetch WebSearch < /dev/null > "$res/run.json" 2>/dev/null
echo "orchestrator cost: \$$(jq -r '.total_cost_usd // "?"' "$res/run.json")  turns: $(jq -r '.num_turns // "?"' "$res/run.json")"
jq -r '.modelUsage // {} | to_entries[] | "  \(.key): $\(.value.costUSD)"' "$res/run.json"

[ -f "$res/proposals.json" ] || { echo "FAIL: no proposals.json written"; exit 1; }
python3 "$here/check_proposals.py" "$res/proposals.json" --digest "$res/digest.json" --workspace-root "$root"
