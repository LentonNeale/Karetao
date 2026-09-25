#!/usr/bin/env bash
# Start the ICM GUI (local only, http://127.0.0.1:PORT/).
# Usage: gui.sh [--demo] [--demo-reset] [--as LOGIN] [--port N] [--check]
#   --demo        serve demo data from $ICM_GUI_DEMO (default /tmp/icm-gui-demo), copied from
#                 gui/fixtures/demo on first use and kept, so several servers and the CLI share it
#   --demo-reset  recopy the demo data first (implies --demo)
#   --as LOGIN    viewer login from people.md (default: gh api user)
#   --check       start, fetch /pipeline, stop; exit 0 on success
set -euo pipefail
ws="$(cd "$(dirname "$0")/.." && pwd)"

demo=false reset=false login="" port=8765 check=false
while [ $# -gt 0 ]; do
  case "$1" in
    --demo) demo=true; shift ;;
    --demo-reset) demo=true; reset=true; shift ;;
    --as) login="$2"; shift 2 ;;
    --port) port="$2"; shift 2 ;;
    --check) check=true; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if $demo; then
  root="${ICM_GUI_DEMO:-/tmp/icm-gui-demo}"
  if $reset || [ ! -d "$root/stages" ]; then
    rm -rf "$root"; mkdir -p "$root"
    cp -r "$ws/gui/fixtures/demo/." "$root/"
  fi
  project="$root/icm-project"
  echo "Demo data: $root  (use it as --root for scripts/review.py and scripts/helper.py)"
else
  root="$ws"
  project="$ws/../icm-project"
fi

[ -f "$project/people.md" ] || { echo "people.md not found at $project/people.md" >&2; exit 1; }
if [ -z "$login" ]; then
  login=$(gh api user --jq .login 2>/dev/null) || { echo "--as LOGIN is required (gh not available)" >&2; exit 1; }
fi
role=$(awk -F'|' -v l="$login" '{gsub(/ /,"",$2); gsub(/ /,"",$3)} $2==l {print $3; exit}' "$project/people.md")
[ -n "$role" ] || { echo "unknown login '$login' (not in $project/people.md)" >&2; exit 1; }

start_page="/"; [ "$role" = helper ] && start_page="/helper"
server=(python3 "$ws/gui/server.py" --root "$root" --project "$project" --as "$role:$login" --port "$port")

if ! $check; then
  echo "Open http://127.0.0.1:$port$start_page  (viewing as $role:$login; Ctrl+C to stop)"
  exec "${server[@]}"
fi

"${server[@]}" >/dev/null 2>&1 &
pid=$!
trap 'kill $pid 2>/dev/null; wait $pid 2>/dev/null || true' EXIT
for _ in $(seq 1 25); do
  sleep 0.2
  [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/pipeline" || true)" = 200 ] && { echo "check ok"; exit 0; }
done
echo "check failed: server did not answer on port $port" >&2
exit 1
