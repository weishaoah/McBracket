#!/usr/bin/env bash
# Focused evidence run: PNG export, card render, console errors, desktop
# layout. Kept short on purpose — one chain, default session.
set -u
BASE="${1:-http://127.0.0.1:5173/}"
AB="agent-browser"
export AGENT_BROWSER_DOWNLOAD_PATH="G:/WorkBuddy/McBracket/shots"
OUT="docs/audit"
mkdir -p "$OUT" shots

$AB open "$BASE"
$AB wait --load networkidle
$AB set viewport 390 844
$AB console --clear
$AB click "[data-testid=start]"
$AB wait 400
for i in 1 2 3 4 5 6 7; do
  $AB click "[data-testid=pick-a]"
  $AB wait 250
  $AB click "[data-testid=next]"
  $AB wait 250
done
echo -n "champion: "; $AB eval "document.querySelector('[data-testid=champion-name]')?.textContent"
echo -n "png data url length: "; $AB eval "window.__mcbracketDebug.pngLength()"
# Reveal the offscreen export stage for a screenshot. Hide the champion
# section only — the stage itself lives inside .app, so hiding .app would
# hide the card too.
$AB eval "(()=>{const c=document.querySelector('.champion');if(c)c.style.display='none';const s=document.querySelector('.export-stage');s.style.left='0';s.style.position='relative';return 'shown'})()"
$AB wait 400
$AB screenshot "$OUT/audit-07-card-render.png"
$AB eval "(()=>{const c=document.querySelector('.champion');if(c)c.style.display='';const s=document.querySelector('.export-stage');s.style.left='-20000px';s.style.position='fixed';return 'restored'})()"
$AB download "[data-testid=export]" shots/audit-champion-card.png
$AB set viewport 1280 800
$AB wait 400
$AB screenshot "$OUT/audit-08-desktop.png"
echo "== console =="
$AB console
echo "export evidence done"
