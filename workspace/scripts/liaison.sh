#!/usr/bin/env bash
# Start a Client Liaison session in a tmux window with panels.
# The main panel runs the client-liaison agent on Haiku, with no shell, web or subagent tools,
# and file writes pre-approved only for intake briefs. A secondary panel provides shell access.
# Usage: workspace/scripts/liaison.sh [first message]
set -euo pipefail
. "$(dirname "$0")/_env.sh"
cd "$ICM_ROOT"

ws="$(basename "$ICM_WORKSPACE")"
settings=$(printf '{"permissions":{"allow":["Edit(%s/stages/01-intake/output/**)"]}}' "$ws")

liaison=(claude --agent client-liaison --model haiku --disallowedTools Bash WebFetch WebSearch Agent NotebookEdit --settings "$settings")

# Headless use (tests, other agents, the GUI) has no terminal for tmux: run the liaison directly.
if [ ! -t 0 ] || [ ! -t 1 ] || [ "${1:-}" = "-p" ] || [ "${1:-}" = "--print" ] || ! command -v tmux >/dev/null; then
  exec "${liaison[@]}" "$@"
fi

# Create a tmux session with a descriptive name
SESSION_NAME="liaison-$(date +%s)"

# Create the session with the first window and split it into two panels
tmux new-session -d -s "$SESSION_NAME" -x 250 -y 50
tmux split-window -t "$SESSION_NAME" -h

# Set pane titles
tmux select-pane -t "$SESSION_NAME:0.0" -T "Client Liaison Agent"
tmux select-pane -t "$SESSION_NAME:0.1" -T "Scratchpad Shell"

# Send commands to each pane
tmux send-keys -t "$SESSION_NAME:0.0" "cd '$ICM_ROOT'" Enter
tmux send-keys -t "$SESSION_NAME:0.1" "cd '$ICM_ROOT' && bash" Enter

# Small delay to ensure panes are ready, then run the liaison command
sleep 0.5
tmux send-keys -t "$SESSION_NAME:0.0" \
  "echo '=== Client Liaison Agent ===' && $(printf '%q ' "${liaison[@]}" "$@")" \
  Enter

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
