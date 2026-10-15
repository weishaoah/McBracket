#!/usr/bin/env python3
"""Collect a real McDonald's MCP snapshot for McBracket.

Read-only by construction: only query-nearby-stores, query-meals,
query-meal-detail, list-nutrition-foods, calculate-price and now-time-info are
ever called, and the write tools are never referenced.

Usage:
    MCD_MCP_TOKEN=xxx python scripts/fetch_snapshot.py \
        --city 上海 --keyword 人民广场 --out src/data/snapshot.json

The token is read from the environment (or ~/.workbuddy/mcp.json) and is never
written into the snapshot.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

ENDPOINT = 'https://mcp.mcd.cn'
READ_ONLY = {
    'query-nearby-stores', 'query-meals', 'query-meal-detail',
    'list-nutrition-foods', 'calculate-price', 'now-time-info',
}
WRITE_TOOLS = {
    'create-order', 'cancel-order', 'mall-create-order', 'party-order-create',
    'draw-lottery', 'auto-bind-coupons', 'delivery-create-address',
}

# Eight seeds chosen for spread across price band and category. Anything not
# present in the fetched menu, or without an exact nutrition-table match, is
# dropped rather than invented.
SEED_CODES = ['1100', '511781', '4648', '1600', '1450', '520445', '2430', '6102']


# --------------------------------------------------------------------------- #
# transport
# --------------------------------------------------------------------------- #
class McpError(RuntimeError):
    pass


def load_token() -> str:
    tok = os.environ.get('MCD_MCP_TOKEN')
    if tok:
        return tok.strip()
    cfg = Path.home() / '.workbuddy' / 'mcp.json'
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding='utf-8'))
            headers = data['mcpServers']['mcd-mcp']['headers']
            auth = headers['Authorization']
            if auth.lower().startswith('bearer '):
                return auth[7:].strip()
        except Exception:
            pass
    raise McpError('No MCP token. Set MCD_MCP_TOKEN or configure ~/.workbuddy/mcp.json.')


class Mcp:
    def __init__(self, token: str):
        self.token = token
        self.calls: list[str] = []

    def call(self, name: str, args: dict, retries: int = 3):
        if name in WRITE_TOOLS:
            raise McpError(f'refusing write tool {name}')
        self.calls.append(name)
        body = json.dumps({'jsonrpc': '2.0', 'id': int(time.time() * 1000) % 10**9,
                           'method': 'tools/call',
                           'params': {'name': name, 'arguments': args}}).encode()
        last = None
        for attempt in range(retries):
            req = urllib.request.Request(
                ENDPOINT, data=body, method='POST',
                headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                         'Authorization': f'Bearer {self.token}'})
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    raw = resp.read().decode('utf-8', 'replace')
                return self._decode(raw)
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in (401, 403):
                    break
                time.sleep(1.5 * (attempt + 1))
            except Exception as exc:  # transient network hiccup
                last = exc
                time.sleep(1.5 * (attempt + 1))
        raise McpError(f'{name} failed: {last}')

    @staticmethod
    def _decode(raw: str):
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith('data:'):
                line = line[5:].strip()
            if not line or not line.startswith('{'):
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue
            if 'result' in msg:
                return msg['result']
            if 'error' in msg:
                raise McpError(f'MCP error: {msg["error"]}')
        return raw


# --------------------------------------------------------------------------- #
# parsing (same traps the doctor project hit: glossary placeholders, mixed text)
# --------------------------------------------------------------------------- #
def scan_balanced_json(text: str):
    """Return the first balanced {...} that parses, tolerating a text prologue."""
    starts = [i for i, ch in enumerate(text) if ch == '{']
    starts.sort(key=lambda i: (0 if i > text.find('Original Response') else 1, i))
    for start in starts:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        break
    return None


def unwrap(raw):
    """Normalise any tool return shape into the business payload dict."""
    if isinstance(raw, dict) and 'content' in raw:
        chunks = raw.get('content') or []
        text = '\n'.join(c.get('text', '') for c in chunks if isinstance(c, dict))
    elif isinstance(raw, str):
        text = raw
    else:
        text = json.dumps(raw, ensure_ascii=False)
    obj = scan_balanced_json(text)
    if obj is None:
        raise McpError('unparseable response')
    if 'success' in obj or 'data' in obj:
        return obj
    return obj


def business_ok(obj) -> bool:
    return isinstance(obj, dict) and obj.get('success') is True


def yuan_to_cents(value) -> int | None:
    """Menu prices arrive as strings in yuan ('25.5'); quotes arrive as cents."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        return int(round(Decimal(str(f)) * 100))
    s = str(value).strip().replace('¥', '').replace('元', '')
    try:
        return int(round(Decimal(s) * 100))
    except Exception:
        return None


def as_records(data, *keys):
    """`data` is sometimes a bare list, sometimes {"stores": [...]}."""
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        for k in keys:
            v = data.get(k)
            if isinstance(v, list):
                return [d for d in v if isinstance(d, dict)]
            if isinstance(v, dict):
                return [v]
        return [data]
    return []


def parse_nutrition_csv(payload) -> dict[str, dict]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, str):
        rows = []
        for line in payload.split('\n')[1:]:
            line = line.strip()
            if not line or line.startswith('['):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 9:
                rows.append({'productName': parts[0], 'energyKcal': parts[3],
                             'protein': parts[4], 'fat': parts[5],
                             'carbohydrate': parts[6], 'sodium': parts[7]})
    else:
        rows = []
    out = {}
    for r in rows:
        name = r.get('productName')
        if not name or name in out:
            continue
        try:
            out[name] = {
                'energyKcal': int(r.get('energyKcal') or 0),
                'protein': float(r.get('protein') or 0),
                'fat': float(r.get('fat') or 0),
                'carbohydrate': float(r.get('carbohydrate') or 0),
                'sodium': int(r.get('sodium') or 0),
            }
        except Exception:
            continue
    return out


# --------------------------------------------------------------------------- #
# collection
# --------------------------------------------------------------------------- #
def collect(city: str, keyword: str, store_code: str | None, out_path: Path):
    mcp = Mcp(load_token())
    tools_used: list[str] = []

    clock = unwrap(mcp.call('now-time-info', {})); tools_used.append('now-time-info')
    official = clock.get('data') if business_ok(clock) else None

    stores_raw = unwrap(mcp.call('query-nearby-stores',
                                 {'beType': 1, 'searchType': 2, 'city': city, 'keyword': keyword}))
    tools_used.append('query-nearby-stores')
    stores = as_records(stores_raw.get('data'), 'stores')
    if not stores:
        raise McpError('no stores returned')

    chosen = None
    if store_code:
        chosen = next((s for s in stores if str(s.get('storeCode')) == store_code), None)
    if chosen is None:
        chosen = stores[0]

    code = str(chosen.get('storeCode'))
    name = chosen.get('storeName') or code

    menu_obj = unwrap(mcp.call('query-meals', {'storeCode': code, 'orderType': 1, 'beType': 1}))
    tools_used.append('query-meals')
    raw_meals = (menu_obj.get('data') or {}).get('meals') if business_ok(menu_obj) else None
    meals: dict[str, dict] = {}
    if isinstance(raw_meals, dict):
        meals = {k: v for k, v in raw_meals.items() if isinstance(v, dict)}
    else:
        for rec in as_records(raw_meals):
            key = str(rec.get('code') or rec.get('productCode') or '')
            if key:
                meals[key] = rec
    if not meals:
        raise McpError(f'store {code} returned an empty menu (probably outside business hours)')

    nut_obj = unwrap(mcp.call('list-nutrition-foods', {}))
    tools_used.append('list-nutrition-foods')
    nutrition = parse_nutrition_csv((nut_obj.get('data') or {}) if isinstance(nut_obj.get('data'), dict)
                                    else nut_obj.get('data')) if business_ok(nut_obj) else {}
    if not nutrition:
        nutrition = parse_nutrition_csv(nut_obj.get('data'))

    items = []
    dropped: dict[str, str] = {}
    for sku in SEED_CODES:
        entry = meals.get(sku)
        if not isinstance(entry, dict):
            # Happens for real: McDonald's swaps the menu by daypart, so burger
            # seeds are absent from the breakfast menu before ~10:30.
            dropped[sku] = 'not on the menu at this daypart'
            continue
        title = entry.get('name') or entry.get('productName')
        if not title:
            dropped[sku] = 'menu entry has no name'
            continue
        menu_cents = yuan_to_cents(entry.get('currentPrice'))
        quote_cents = None
        quote_ok = False
        quote_note = None
        try:
            q = unwrap(mcp.call('calculate-price', {
                'storeCode': code, 'orderType': 1, 'beType': 1,
                'items': [{'productCode': sku, 'quantity': 1}]}))
            tools_used.append('calculate-price')
            if business_ok(q):
                d = q.get('data') or {}
                cand = d.get('totalPrice', d.get('price'))
                if cand is None:
                    pl = d.get('productList') or []
                    if pl:
                        cand = pl[0].get('price')
                quote_cents = int(cand) if isinstance(cand, (int, float)) else None
                quote_ok = quote_cents is not None and quote_cents > 0
                if not quote_ok:
                    quote_note = 'calculate-price returned no positive total'
            else:
                quote_note = f"calculate-price business failure: {q.get('code')}"
        except McpError as exc:
            quote_note = f'calculate-price transport error: {exc}'

        nut = nutrition.get(title)
        items.append({
            'code': sku,
            'name': title,
            'menuPriceCents': menu_cents,
            'quotePriceCents': quote_cents if quote_ok else None,
            'quoteNote': quote_note,
            'priceSource': 'calculate-price' if quote_ok else ('query-meals' if menu_cents else 'none'),
            'nutrition': nut,          # None => render as "暂无可靠数据"
            'nutritionMatch': 'exact' if nut else 'none',
            'collectedAt': (official or {}).get('formatted') or (official or {}).get('datetime'),
        })

    snapshot = {
        'schema': 'mcbracket/snapshot@1',
        # `mode` describes how the *page* gets its data, not how this file was
        # produced. The web app always reads this static file, so claiming
        # 'live' here would render "实时查询" next to data that is really a
        # snapshot. `capturedWith` records that a real MCP run produced it.
        'mode': 'demo-snapshot',
        'capturedWith': 'official-mcp',
        'endpoint': ENDPOINT,
        'collectedAt': (official or {}).get('formatted') or (official or {}).get('datetime'),
        'collectedAtTimezone': (official or {}).get('timezone', 'GMT+08:00'),
        'store': {'code': code, 'name': name,
                  'city': city, 'businessStatus': chosen.get('businessStatus')},
        # Every figure below comes from this one channel, so prices are only
        # ever compared within identical store + order-type conditions.
        'orderType': '堂食/到店取餐渠道（orderType=1, beType=1）',
        'notes': (
            '菜单价格来自 query-meals（单位：元，字符串）；核价来自 calculate-price'
            '（单位：分，整数）。两者单位不同，已统一换算为分后比较。'
            '营养数据来自 list-nutrition-foods，仅采用商品名精确匹配项，'
            '未匹配一律显示「暂无可靠数据」。'
            '麦当劳菜单按营业时段切换（如早餐时段不供应汉堡），'
            '因此快照可能是分批采集的，每条数据保留各自的采集时间。'
        ),
        'toolsUsed': sorted(set(tools_used)),
        'items': items,
    }

    # ---- merge with the previous snapshot ---------------------------------- #
    # The menu is daypart-dependent (breakfast has no burgers), so a single run
    # cannot always see all eight seeds. Merging keeps whatever a previous run
    # captured instead of silently downgrading the snapshot to one item.
    prev = None
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            prev = None

    merged, carried, refreshed = merge_items(items, prev)
    snapshot['items'] = merged

    # When rows come from more than one run, say so: a single "collectedAt"
    # would overstate how fresh most of the data is.
    stamps = sorted({r.get('collectedAt') for r in merged if r.get('collectedAt')})
    if len(stamps) > 1:
        snapshot['collectedFrom'] = stamps[0]
        snapshot['collectedTo'] = stamps[-1]
    snapshot['coverage'] = {
        'requested': len(SEED_CODES),
        'freshThisRun': len(items),
        'carriedFromPrevious': len(carried),
        'missing': sorted(set(SEED_CODES) - {i['code'] for i in merged}),
    }
    if dropped:
        snapshot['coverage']['droppedThisRun'] = dropped
    if prev:
        snapshot['previousCollectedAt'] = prev.get('collectedAt')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'store  : {name} ({code})')
    print(f'time   : {snapshot["collectedAt"]} {snapshot["collectedAtTimezone"]}')
    print(f'tools  : {snapshot["toolsUsed"]}')
    print(f'fresh  : {len(items)}/{len(SEED_CODES)}   '
          f'carried: {len(carried)}   total: {len(merged)}/{len(SEED_CODES)}')
    for it in merged:
        nut = it['nutrition']
        tag = ' ' if it['code'] in {i['code'] for i in items} else '~'
        print(f" {tag}{it['code']:>10} {it['name']:<14} "
              f"menu={'-' if it['menuPriceCents'] is None else it['menuPriceCents']/100:>6} "
              f"quote={'-' if it['quotePriceCents'] is None else it['quotePriceCents']/100:>6} "
              f"kcal={'-' if not nut else nut['energyKcal']:>4} match={it['nutritionMatch']}")
    for sku, why in dropped.items():
        print(f"  - {sku}: {why}")
    print('  (~ = carried over from the previous snapshot)')
    print(f'written: {out_path}')
    return snapshot


def merge_items(fresh: list[dict], prev: dict | None):
    """Keep the best evidence per seed code across runs.

    A fresh row wins when it carries more information than the previous one
    (a verified quote beats a menu-only price). Otherwise the previous row is
    carried over, so a breakfast-hour run never erases a lunch-hour capture.
    Returns (merged, carried_codes, refreshed_codes).
    """
    prev_rows = {r['code']: r for r in ((prev or {}).get('items') or [])}
    fresh_codes = {r['code'] for r in fresh}

    merged: list[dict] = []
    carried: list[str] = []
    refreshed: list[str] = []

    for row in fresh:
        old = prev_rows.get(row['code'])
        if old and _score(old) > _score(row):
            kept = dict(old)
            kept.setdefault('collectedAt', (prev or {}).get('collectedAt'))
            merged.append(kept)
            carried.append(row['code'])
        else:
            merged.append(row)
            if old:
                refreshed.append(row['code'])

    prev_at = (prev or {}).get('collectedAt')
    for code, row in prev_rows.items():
        if code not in fresh_codes:
            row = dict(row)
            # A carried row keeps the timestamp it was actually captured at, so
            # the snapshot never implies it is fresher than it is.
            row.setdefault('collectedAt', prev_at)
            merged.append(row)
            carried.append(code)

    merged.sort(key=lambda r: SEED_CODES.index(r['code']) if r['code'] in SEED_CODES else 99)
    return merged, carried, refreshed


def _score(row: dict) -> int:
    """Evidence ranking: verified quote > menu price > anything else."""
    s = 0
    if row.get('quotePriceCents'):
        s += 4
    if row.get('menuPriceCents'):
        s += 2
    if row.get('nutrition'):
        s += 1
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--city', default='上海')
    ap.add_argument('--keyword', default='人民广场')
    ap.add_argument('--store', default=None)
    ap.add_argument('--out', default='src/data/snapshot.json')
    args = ap.parse_args()
    try:
        collect(args.city, args.keyword, args.store, Path(args.out))
    except McpError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
