#!/usr/bin/env bash
# Pre-release browser audit. Everything runs in ONE chain because the
# browser daemon resets page state between unrelated invocations.
#
# Checks, on a 390x844 phone viewport:
#   1. home shows the roster, the menu-reference-price label, the carried
#      row's real capture date, and the non-live notice
#   2. a full 7-match playthrough advances correctly (7 bracket matches,
#      7 winners, a champion with a 3-step route)
#   3. restart returns to match 1
#   4. the champion card PNG export produces a real file
#   5. no console errors along the way
set -u
BASE="${1:-http://127.0.0.1:5173/}"
AB="agent-browser"
export AGENT_BROWSER_DOWNLOAD_PATH="G:/WorkBuddy/McBracket/shots"
# Isolated session: a wedged default daemon must not poison the audit.
export AGENT_BROWSER_SESSION="mcbracket-audit"
OUT="docs/audit"
mkdir -p "$OUT" shots

echo "== home (390x844) =="
$AB set viewport 390 844
$AB open "$BASE"
$AB wait --load networkidle
$AB console --clear
$AB screenshot "$OUT/audit-01-home.png"
echo -n "roster items: "; $AB eval "document.querySelectorAll('.roster-item').length"
echo -n "menu-reference label: "; $AB eval "document.body.innerText.includes('菜单参考价') ? 'yes' : 'MISSING'"
echo -n "carried capture date: "; $AB eval "document.body.innerText.includes('10-14') ? 'yes' : 'MISSING'"
echo -n "non-live notice: "; $AB eval "document.body.innerText.includes('非实时') ? 'yes' : 'MISSING'"

echo "== match 1 + data reveal =="
$AB click "[data-testid=start]"
$AB wait 500
$AB screenshot "$OUT/audit-02-match1.png"
$AB click "[data-testid=pick-a]"
$AB wait 700
$AB screenshot "$OUT/audit-03-reveal.png"
echo -n "reveal provenance: "; $AB eval "document.querySelector('[data-testid=reveal]')?.innerText.includes('官方核价') ? 'yes' : 'MISSING'"

echo "== matches 2..7 =="
for i in 2 3 4 5 6 7; do
  $AB click "[data-testid=next]"
  $AB wait 350
  $AB click "[data-testid=pick-a]"
  $AB wait 350
done
$AB screenshot "$OUT/audit-04-match7.png"
$AB click "[data-testid=next]"
$AB wait 700
$AB screenshot "$OUT/audit-05-champion.png"

echo "== champion page facts =="
echo -n "champion: "; $AB eval "document.querySelector('[data-testid=champion-name]')?.textContent"
echo -n "bracket matches: "; $AB eval "document.querySelectorAll('.bracket-match').length"
echo -n "bracket winners: "; $AB eval "document.querySelectorAll('.bracket-cell.winner').length"
echo -n "route steps: "; $AB eval "document.querySelectorAll('.route-item').length"
echo -n "snapshot notice: "; $AB eval "document.body.innerText.includes('官方数据快照') ? 'yes' : 'MISSING'"

echo "== restart =="
$AB click "[data-testid=restart]"
$AB wait 500
echo -n "progress after restart: "; $AB eval "document.querySelector('[data-testid=progress]')?.textContent ?? 'no-progress'"
$AB screenshot "$OUT/audit-06-restart.png"

echo "== replay + PNG export =="
for i in 1 2 3 4 5 6 7; do
  $AB click "[data-testid=pick-a]"
  $AB wait 300
  $AB click "[data-testid=next]"
  $AB wait 300
done
echo -n "champion after replay: "; $AB eval "document.querySelector('[data-testid=champion-name]')?.textContent"
echo -n "png data url length: "; $AB eval "window.__mcbracketDebug.pngLength()"
$AB eval "(()=>{const s=document.querySelector('.export-stage');s.style.left='0';s.style.position='relative';document.querySelector('.app').style.display='none';return 'shown'})()"
$AB wait 400
$AB screenshot "$OUT/audit-07-card-render.png"
$AB eval "(()=>{const s=document.querySelector('.export-stage');s.style.left='-20000px';s.style.position='fixed';document.querySelector('.app').style.display='';return 'restored'})()"
$AB download "[data-testid=export]" shots/audit-champion-card.png
ls -la shots/audit-champion-card.png 2>/dev/null || echo "NO FILE"

echo "== desktop width =="
$AB set viewport 1280 800
$AB wait 400
$AB screenshot "$OUT/audit-08-desktop.png"

echo "== console =="
$AB console
echo "audit done"
