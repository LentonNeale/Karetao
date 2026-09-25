#!/usr/bin/env bash
# Run the client-liaison scenarios through one-shot Haiku sessions and check the results.
# Transcripts and any briefs are saved in tests/liaison/results/ for review.
# Usage: tests/liaison/run.sh [scenario-name-substring]
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
ws="$(cd "$here/../.." && pwd)"
out="$ws/stages/01-intake/output"
res="$here/results"
mkdir -p "$res"
front() { sed -n '/^---$/,/^---$/p' "$1" | sed -n "s/^$2: *//p" | tr -d '"'; }
body() { awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$1"; }

pass=0 fail=0
for f in "$here"/scenarios/*.md; do
  name=$(basename "$f" .md)
  [ -n "${1:-}" ] && [[ $name != *"$1"* ]] && continue
  slug="test-$name" brief="$out/test-$name-brief.md"
  rm -f "$brief"
  want=$(front "$f" expect_brief) contains=$(front "$f" expect_output_contains)
  prompt="$(body "$f")

(Test harness: if you write a brief, use the slug \`$slug\`.)"

  timeout 300 "$ws/scripts/liaison.sh" -p "$prompt" > "$res/$name.txt" 2>&1
  errs=()
  case $want in
    none)  [ -e "$brief" ] && errs+=("a brief was written but none was expected") ;;
    ready) [ -e "$brief" ] || errs+=("no brief written")
           [ -e "$brief" ] && ! grep -qiE '^status:[[:space:]]*ready[[:space:]]*$' "$brief" && errs+=("status is not 'ready'")
           for h in "Goal" "Done when" "Out of scope" "Evidence"; do
             [ -e "$brief" ] && ! grep -qi "$h" "$brief" && errs+=("brief lacks '$h'"); done ;;
    ready-with-gaps)
           [ -e "$brief" ] || errs+=("no brief written")
           [ -e "$brief" ] && ! grep -qiE '^status:[[:space:]]*ready-with-gaps' "$brief" && errs+=("status is not 'ready-with-gaps'")
           [ -e "$brief" ] && ! grep -qi "gaps" "$brief" && errs+=("brief has no Gaps section") ;;
  esac
  [ -n "$contains" ] && ! grep -qiF -- "$contains" "$res/$name.txt" && errs+=("reply lacks '$contains'")
  [ -e "$brief" ] && grep -qE '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}' "$brief" && errs+=("brief contains an email address")
  [ -e "$brief" ] && mv "$brief" "$res/$name-brief.md"

  if [ ${#errs[@]} -eq 0 ]; then echo "PASS  $name"; pass=$((pass+1))
  else echo "FAIL  $name: $(IFS='; '; echo "${errs[*]}")"; fail=$((fail+1)); fi
done
echo "---"; echo "$pass passed, $fail failed. Transcripts: ${res#$ws/}/"
[ $fail -eq 0 ]
