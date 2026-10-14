#!/usr/bin/env bash
# Drives one complete 7-match playthrough in a real browser.
# Usage: bash scripts/playthrough.sh [base-url]
set -u
BASE="${1:-http://127.0.0.1:5173/}"
SHOTS="shots"
AB="agent-browser"
mkdir -p "$SHOTS"

run() { echo "\$ $*"; "$AB" "$@"; echo; }

run viewport 390 844
run open "$BASE"
run wait --load networkidle
run console --clear
run screenshot "$SHOTS/01-home.png"

run click "[data-testid=start]"
run wait 600
run screenshot "$SHOTS/02-first-match.png"

for i in 1 2 3 4 5 6 7; do
  run click "[data-testid=pick-a]"
  run wait 700
  run screenshot "$SHOTS/1${i}-picked.png"
  run click "[data-testid=next]"
  run wait 700
done

run screenshot "$SHOTS/20-champion.png"
run click "[data-testid=export]"
run wait 4000
run screenshot "$SHOTS/21-after-export.png"

echo "==== console ===="
run console
echo "==== champion name ===="
run eval "document.querySelector('[data-testid=champion-name]')?.textContent"
echo "==== progress text ===="
run eval "document.querySelector('[data-testid=progress]')?.textContent"
echo "done"
