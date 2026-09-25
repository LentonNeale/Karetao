#!/usr/bin/env bash
# Start a Client Liaison session: the main thread runs as the client-liaison agent on Haiku,
# with no shell, web or subagent tools, and file writes pre-approved only for intake briefs.
# Usage: workspace/scripts/liaison.sh [first message]
set -euo pipefail
. "$(dirname "$0")/_env.sh"
cd "$ICM_ROOT"

ws="$(basename "$ICM_WORKSPACE")"
settings=$(printf '{"permissions":{"allow":["Edit(%s/stages/01-intake/output/**)"]}}' "$ws")

exec claude \
  --agent client-liaison \
  --model haiku \
  --disallowedTools Bash WebFetch WebSearch Agent NotebookEdit \
  --settings "$settings" \
  "$@"
