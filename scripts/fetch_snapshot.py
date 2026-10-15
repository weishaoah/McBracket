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
from datetime import datetime
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
# dropped rather than invented. The roster is fixed at these eight codes: a
# merge must never grow or shrink it silently.
SEED_CODES = ['1100', '511781', '4648', '1600', '1450', '520445', '2430', '6102']
SEED_SET = set(SEED_CODES)

# The one channel this snapshot is allowed to describe. Prices from a
# different store or a different ordering channel are not comparable with
# these, so a previous snapshot is only merged when it matches exactly.
CHANNEL = {'orderType': 1, 'beType': 1}
CHANNEL_LABEL = '堂食/到店取餐渠道（orderType=1, beType=1）'

# A carried-over row older than this is dropped rather than shown: a week-old
# price is not "current data" and displaying it as such would mislead.
STALE_AFTER_DAYS = 7

# Nutrient columns kept from the official table, with their natural types.
NUTRIENT_FIELDS = (('energyKcal', int), ('protein', float), ('fat', float),
                   ('carbohydrate', float), ('sodium', int))


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


def to_int_cents(value) -> int | None:
    """calculate-price is documented as integer cents; tolerate numeric strings."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    return int(s) if s.isdigit() else None


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


def _to_number(value, cast):
    """Missing means missing.

    A real 0 in the official table (diet cola 0 kcal, apple slices 0 mg
    sodium) must stay 0; only an absent or empty cell becomes None so the UI
    can render 「暂无可靠数据」instead of a fabricated zero.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return cast(s)
    except (TypeError, ValueError):
        return None


def _parse_header(line: str) -> list[str] | None:
    """`[160]{productName,nutritionDescription,...,calcium}:` -> column names."""
    m = re.search(r'\{([^}]*)\}', line)
    if not m:
        return None
    cols = [c.strip() for c in m.group(1).split(',') if c.strip()]
    return cols or None


def parse_nutrition_csv(payload) -> dict[str, dict]:
    """Official nutrition table -> {productName: {field: number | None}}.

    The table arrives as a header line plus CSV rows inside a JSON string.
    Columns are located from the header when present, so a reordered or
    extended table cannot silently shift values into the wrong field, and a
    row whose field count does not match the header is skipped instead of
    being mis-parsed. Absent cells stay None — never 0.
    """
    if isinstance(payload, dict):
        inner = payload.get('data')
        payload = inner if inner is not None else payload
    if isinstance(payload, list):
        rows = [r for r in payload if isinstance(r, dict)]
        header = None
    elif isinstance(payload, str):
        header = None
        rows = []
        for line in payload.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('['):
                header = _parse_header(line)
                continue
            parts = [p.strip() for p in line.split(',')]
            if header and len(parts) == len(header):
                rows.append(dict(zip(header, parts)))
            elif not header and len(parts) >= 9:
                rows.append({'productName': parts[0], 'energyKcal': parts[3],
                             'protein': parts[4], 'fat': parts[5],
                             'carbohydrate': parts[6], 'sodium': parts[7]})
            else:
                print(f'  ! nutrition row skipped (field count mismatch): {line[:60]}',
                      file=sys.stderr)
    else:
        rows = []
        header = None

    out: dict[str, dict] = {}
    for r in rows:
        name = r.get('productName')
        if not name or name in out:
            continue
        out[name] = {field: _to_number(r.get(field), cast) for field, cast in NUTRIENT_FIELDS}
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
    nutrition = parse_nutrition_csv(nut_obj.get('data')) if business_ok(nut_obj) else {}

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
                quote_cents = to_int_cents(cand)
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
            'carried': False,          # set True by the merge when a row survives
                                        # from an earlier run because today's
                                        # menu did not carry the item
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
        # Machine-readable channel, checked before any cross-run merge so a
        # snapshot from another store or channel can never bleed prices in.
        'channel': dict(CHANNEL),
        # Every figure below comes from this one channel, so prices are only
        # ever compared within identical store + order-type conditions.
        'orderType': CHANNEL_LABEL,
        'notes': (
            '菜单价格来自 query-meals（单位：元，字符串）；核价来自 calculate-price'
            '（单位：分，整数）。两者单位不同，已统一换算为分后比较。'
            '营养数据来自 list-nutrition-foods，仅采用商品名精确匹配项；'
            '官方营养表中缺失的字段显示 null（页面渲染为「暂无可靠数据」），'
            '不会被当成 0。'
            '麦当劳菜单按营业时段切换（如早餐时段不供应汉堡），'
            '因此快照可能是分批采集的：每条数据保留各自的采集时间，'
            '合并时只接受同一门店、同一渠道的历史数据，超过 '
            f'{STALE_AFTER_DAYS} 天的旧行会被丢弃而不是继续展示。'
        ),
        'toolsUsed': sorted(set(tools_used)),
        'items': items,
    }

    # ---- merge with the previous snapshot ---------------------------------- #
    # The menu is daypart-dependent (breakfast has no burgers), so a single run
    # cannot always see all eight seeds. Merging keeps whatever a previous run
    # captured instead of silently downgrading the snapshot to one item —
    # but only when the previous file describes the SAME store and channel,
    # because prices are not comparable across either.
    prev = None
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            prev = None

    merge_notes: list[str] = []
    if prev and not compatible_previous(prev, code, CHANNEL, CHANNEL_LABEL):
        merge_notes.append('previous snapshot ignored: different store or channel')
        prev = None

    now_stamp = (official or {}).get('formatted') or (official or {}).get('datetime')
    merged, carried, refreshed, merge_notes = merge_items(
        items, prev, now_stamp, merge_notes)
    snapshot['items'] = merged

    # When rows come from more than one run, say so: a single "collectedAt"
    # would overstate how fresh most of the data is.
    stamps = sorted({r.get('collectedAt') for r in merged if r.get('collectedAt')})
    if len(stamps) > 1:
        snapshot['collectedFrom'] = stamps[0]
        snapshot['collectedTo'] = stamps[-1]
    # Named `lastRun` on purpose: this describes only the run that just
    # happened. After several merges it is not the coverage of the file as a
    # whole, and reading it as such would be misleading.
    snapshot['lastRun'] = {
        'at': now_stamp,
        'requested': len(SEED_CODES),
        'freshThisRun': len(items),
        'carriedFromPrevious': len(carried),
        'refreshedFromPrevious': len(refreshed),
        'missing': sorted(set(SEED_CODES) - {i['code'] for i in merged}),
    }
    if dropped:
        snapshot['lastRun']['droppedThisRun'] = dropped
    if merge_notes:
        snapshot['lastRun']['mergeNotes'] = merge_notes
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
        kcal = nut.get('energyKcal') if nut else None
        print(f" {tag}{it['code']:>10} {it['name']:<14} "
              f"menu={'-' if it['menuPriceCents'] is None else it['menuPriceCents']/100:>6} "
              f"quote={'-' if it['quotePriceCents'] is None else it['quotePriceCents']/100:>6} "
              f"kcal={'-' if kcal is None else kcal:>4} match={it['nutritionMatch']}"
              f"{' carried' if it.get('carried') else ''}")
    for sku, why in dropped.items():
        print(f"  - {sku}: {why}")
    print('  (~ = carried over from the previous snapshot)')
    for note in merge_notes:
        print(f'  * {note}')
    print(f'written: {out_path}')
    return snapshot


def compatible_previous(prev: dict | None, store_code: str, channel: dict,
                        channel_label: str) -> bool:
    """May this previous snapshot be merged into the current run?

    Prices are only comparable inside one store and one ordering channel, so
    a file from a different store — or a different channel — must be ignored
    wholesale rather than merged row by row. Files written before the
    `channel` field existed fall back to comparing the human-readable
    `orderType` label.
    """
    if not isinstance(prev, dict) or not prev.get('items'):
        return False
    if (prev.get('store') or {}).get('code') != store_code:
        return False
    prev_channel = prev.get('channel')
    if prev_channel is None:
        return prev.get('orderType') == channel_label
    return prev_channel == channel


def _age_days(stamp, now_stamp) -> float | None:
    """Age of a `YYYY-MM-DD HH:MM:SS` stamp in days, or None if unparseable."""
    for candidate in (stamp, now_stamp):
        if not isinstance(candidate, str):
            return None
    try:
        then = datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
        now = datetime.strptime(now_stamp, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None
    return (now - then).total_seconds() / 86400.0


def merge_items(fresh: list[dict], prev: dict | None, now_stamp,
                notes: list[str] | None = None,
                max_age_days: int = STALE_AFTER_DAYS):
    """Merge a fresh run into the previous snapshot, field-wise.

    Rules, in order:

    - An item the fresh run could not see at all (absent from today's menu)
      is carried over unchanged, keeping the timestamp it was captured at.
      Rows older than `max_age_days` are dropped instead: a week-old price is
      not current data.
    - An item the fresh run did see: today's observation wins for every
      field it actually carries. The only things inherited from an older row
      are (a) a verified quote that today's run failed to obtain and (b) a
      nutrition-table match, which is global reference data rather than
      store- or time-specific. Both keep the older row's timestamp so the
      page can say when the evidence is really from.
    - Rows outside the eight seeds are never carried: the roster is fixed.

    Returns (merged, carried_codes, refreshed_codes, notes).
    """
    notes = list(notes or [])
    prev_rows = {r['code']: r for r in ((prev or {}).get('items') or [])
                 if isinstance(r, dict) and r.get('code')}
    extra = sorted(set(prev_rows) - SEED_SET)
    if extra:
        notes.append(f'ignored {len(extra)} previous row(s) outside the eight seeds: {extra}')
    prev_rows = {c: r for c, r in prev_rows.items() if c in SEED_SET}

    fresh_by_code = {r['code']: r for r in fresh}
    merged: list[dict] = []
    carried: list[str] = []
    refreshed: list[str] = []

    for code in SEED_CODES:  # fixed roster order
        row = fresh_by_code.get(code)
        old = prev_rows.get(code)

        if row is None:
            if old is None:
                continue
            age = _age_days(old.get('collectedAt'), now_stamp)
            if age is None or age > max_age_days:
                notes.append(f'{code} dropped: last captured {old.get("collectedAt")}, '
                             f'older than {max_age_days} days')
                continue
            kept = dict(old)
            kept['carried'] = True
            merged.append(kept)
            carried.append(code)
            continue

        if old is None:
            merged.append(row)
            continue

        out = dict(row)
        if old.get('quotePriceCents') and not out.get('quotePriceCents'):
            # Today's quote failed; keep the older *verified* quote, but say
            # which run verified it instead of presenting it as today's price.
            out['quotePriceCents'] = old['quotePriceCents']
            out['priceSource'] = 'calculate-price'
            out['quoteCollectedAt'] = old.get('collectedAt')
            out['quoteNote'] = f"verified in an earlier run ({old.get('collectedAt')})"
        if not out.get('nutrition') and old.get('nutrition'):
            out['nutrition'] = old['nutrition']
            out['nutritionMatch'] = old.get('nutritionMatch', 'exact')
        merged.append(out)
        refreshed.append(code)

    return merged, carried, refreshed, notes


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
