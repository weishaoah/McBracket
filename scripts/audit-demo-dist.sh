#!/usr/bin/env bash
# No-token public-demo smoke test against the PRODUCTION build (dist/).
# This is exactly what a visitor to the GitHub Pages demo will run:
# static files, no MCP token, no backend. Includes a real PNG export.
set -u
BASE="${1:-http://127.0.0.1:5174/}"
AB="agent-browser"
export AGENT_BROWSER_DOWNLOAD_PATH="G:/WorkBuddy/McBracket/shots"
OUT="docs/audit"
mkdir -p "$OUT" shots

$AB open "$BASE"
$AB wait --load networkidle
$AB set viewport 390 844
$AB console --clear
$AB screenshot "$OUT/audit-09-demo-home.png"
echo -n "roster items: "; $AB eval "document.querySelectorAll('.roster-item').length"
echo -n "snapshot badge: "; $AB eval "document.body.innerText.includes('官方数据快照') ? 'yes' : 'MISSING'"
echo -n "menu-reference label: "; $AB eval "document.body.innerText.includes('菜单参考价') ? 'yes' : 'MISSING'"
echo -n "non-live notice: "; $AB eval "document.body.innerText.includes('非实时') ? 'yes' : 'MISSING'"
echo -n "no token anywhere: "; $AB eval "document.body.innerText.match(/Bearer|token/i) ? 'LEAK' : 'clean'"

$AB click "[data-testid=start]"
$AB wait 400
for i in 1 2 3 4 5 6 7; do
  $AB click "[data-testid=pick-a]"
  $AB wait 250
  $AB click "[data-testid=next]"
  $AB wait 250
done
echo -n "champion: "; $AB eval "document.querySelector('[data-testid=champion-name]')?.textContent"
$AB screenshot "$OUT/audit-10-demo-champion.png"
$AB download "[data-testid=export]" shots/audit-demo-card.png
ls -la shots/audit-demo-card.png 2>/dev/null || echo "NO FILE"
echo "== console =="
$AB console
echo "dist demo smoke done"
