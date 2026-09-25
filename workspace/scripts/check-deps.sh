#!/usr/bin/env bash
# Check (and optionally install) the tools the workspace and the project need.
# Reads workspace/setup/deps.txt (workspace needs) and icm-project/deps.txt (project needs).
# Line format:  check | apt packages | note      ('#' starts a comment)
#   check = a command name, or an absolute path that must exist
#   apt packages = space-separated, or '-' if not installable with apt (the note says how)
# Usage: check-deps.sh [--install] [--yes]
set -euo pipefail
ws="$(cd "$(dirname "$0")/.." && pwd)"
root="$(cd "$ws/.." && pwd)"
install=0 yes=0
for a in "$@"; do
  case $a in
    --install) install=1 ;;
    --yes|-y) yes=1 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

missing_pkgs=() manual=() n_missing=0
trim() { local s="${1:-}"; s="${s#"${s%%[![:space:]]*}"}"; printf '%s' "${s%"${s##*[![:space:]]}"}"; }
check_file() {
  local src=$1
  [ -f "$src" ] || return 0
  echo "== ${src#$root/}"
  while IFS='|' read -r check pkgs note; do
    check=$(trim "$check"); pkgs=$(trim "${pkgs:-}"); note=$(trim "${note:-}")
    [ -z "$check" ] && continue
    if [[ $check == /* ]]; then [ -e "$check" ] && ok=1 || ok=0
    else command -v "$check" >/dev/null 2>&1 && ok=1 || ok=0; fi
    if [ $ok = 1 ]; then printf '  ok       %s\n' "$check"
    else
      n_missing=$((n_missing+1)); printf '  MISSING  %-34s %s\n' "$check" "${note}"
      if [ "$pkgs" = "-" ] || [ -z "$pkgs" ]; then manual+=("$check: $note")
      else for p in $pkgs; do [[ " ${missing_pkgs[*]:-} " == *" $p "* ]] || missing_pkgs+=("$p"); done; fi
    fi
  done < <(sed -e 's/#.*//' "$src" | grep -v '^[[:space:]]*$')
}
check_file "$ws/setup/deps.txt"
check_file "$root/icm-project/deps.txt"

if [ $n_missing -eq 0 ]; then echo "All dependencies present."; exit 0; fi
echo
[ ${#manual[@]} -gt 0 ] && { echo "Install manually:"; printf '  %s\n' "${manual[@]}"; }
[ ${#missing_pkgs[@]} -gt 0 ] && echo "apt packages needed: ${missing_pkgs[*]}"

if [ $install = 0 ] || [ ${#missing_pkgs[@]} -eq 0 ]; then
  [ $install = 0 ] && [ ${#missing_pkgs[@]} -gt 0 ] && echo "Run with --install to install them."
  exit 1
fi

command -v apt-get >/dev/null || { echo "apt-get not found: install the packages above with your package manager." >&2; exit 1; }
cmd=(sudo apt-get install -y --no-install-recommends "${missing_pkgs[@]}")
echo "Will run: sudo apt-get update && ${cmd[*]}"
if [ $yes = 0 ]; then read -r -p "Proceed? [y/N] " r; [[ $r =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }; fi
sudo apt-get update && "${cmd[@]}"
echo; echo "Re-checking…"; exec "$0"
