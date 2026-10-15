#!/usr/bin/env bash
# Play one full round, then verify the PNG exporter end to end.
# Everything runs in one chain because the browser daemon can reset the page
# between unrelated invocations.
set -u
BASE="${1:-http://127.0.0.1:5173/}"
AB="agent-browser"
export AGENT_BROWSER_DOWNLOAD_PATH="G:/WorkBuddy/McBracket/shots"
mkdir -p shots

echo "== open =="
$AB set viewport 390 844
$AB open "$BASE"
$AB wait --load networkidle

echo "== play 7 matches =="
$AB click "[data-testid=start]"
$AB wait 500
for i in 1 2 3 4 5 6 7; do
  $AB click "[data-testid=pick-a]"
  $AB wait 600
  $AB click "[data-testid=next]"
  $AB wait 600
done

echo "== champion =="
$AB eval "document.querySelector('[data-testid=champion-name]')?.textContent"

echo "== restart returns to match 1 =="
$AB click "[data-testid=restart]"
$AB wait 500
$AB eval "document.querySelector('[data-testid=progress]')?.textContent ?? 'no-progress'"

echo "== replay 7 matches after restart =="
for i in 1 2 3 4 5 6 7; do
  $AB click "[data-testid=pick-a]"
  $AB wait 500
  $AB click "[data-testid=next]"
  $AB wait 500
done
$AB eval "document.querySelector('[data-testid=champion-name]')?.textContent"

echo "== png data check =="
$AB eval "window.__mcbracketDebug.pngLength()"

echo "== make export card visible for screenshot =="
$AB eval "(()=>{const s=document.querySelector('.export-stage');s.style.left='0';s.style.position='relative';document.querySelector('.app').style.display='none';return 'shown'})()"
$AB wait 300
$AB screenshot shots/30-card-render.png

echo "== restore + download via button =="
$AB eval "(()=>{const s=document.querySelector('.export-stage');s.style.left='-20000px';s.style.position='fixed';document.querySelector('.app').style.display='';return 'restored'})()"
$AB download "[data-testid=export]" shots/champion-card.png
ls -la shots/champion-card.png 2>/dev/null || echo "NO FILE"

echo "== console errors =="
$AB console
echo "verify done"
