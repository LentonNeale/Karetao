#!/usr/bin/env bash
# One-time (idempotent) install into the project that contains this workspace:
#  - creates ../icm-project/ from templates if missing
#  - symlinks workspace/agents/*.md into ../.claude/agents/
#  - ensures stage output/ folders exist
set -euo pipefail
ws="$(cd "$(dirname "$0")/.." && pwd)"
root="$(cd "$ws/.." && pwd)"
rel_ws="$(basename "$ws")"

if [ ! -d "$root/icm-project" ]; then
  cp -r "$ws/setup/templates/icm-project" "$root/icm-project"
  echo "created icm-project/ (fill it in via setup/questionnaire.md)"
fi

mkdir -p "$root/.claude/agents"
for f in "$ws"/agents/*.md; do
  ln -sfn "../../$rel_ws/agents/$(basename "$f")" "$root/.claude/agents/$(basename "$f")"
done
echo "linked agents: $(cd "$ws/agents" && ls *.md | tr '\n' ' ')"

for d in "$ws"/stages/*/; do mkdir -p "$d/output" "$d/references"; touch "$d/output/.gitkeep"; done
chmod +x "$ws"/scripts/*.sh "$ws"/scripts/*.py
echo "done"
echo; "$ws/scripts/check-deps.sh" || echo "Some dependencies are missing: run workspace/scripts/check-deps.sh --install"
