export interface Nutrition {
  /**
   * null = the official nutrition table has no value for this field.
   * It is NOT zero: the table really contains 0s (diet cola, apple
   * slices), so "absent" and "0" must stay distinguishable on screen.
   */
  energyKcal: number | null
  protein: number | null
  fat: number | null
  carbohydrate: number | null
  sodium: number | null
}

export type PriceSource = 'calculate-price' | 'query-meals' | 'none'
export type NutritionMatch = 'exact' | 'none'

export interface SnapshotItem {
  code: string
  name: string
  /** Menu price, already converted to cents (query-meals returns yuan strings). */
  menuPriceCents: number | null
  /** Official quote, cents (calculate-price returns cents). */
  quotePriceCents: number | null
  priceSource: PriceSource
  nutrition: Nutrition | null
  nutritionMatch: NutritionMatch
  /** When this row's price evidence was captured; may predate the latest run. */
  collectedAt?: string
  /**
   * True when the row survived from an earlier run because the item was
   * not on the menu when the latest run happened.
   */
  carried?: boolean
  /** When the quote was actually verified, if it came from an earlier run. */
  quoteCollectedAt?: string | null
  quoteNote?: string | null
  /** Category tag used only for labelling; never used to invent data. */
  category?: string
}

export interface Snapshot {
  schema: string
  mode: 'demo-snapshot' | 'live'
  /** How the file itself was produced — distinct from `mode` (how the page reads it). */
  capturedWith?: string
  endpoint: string
  collectedAt: string
  collectedAtTimezone: string
  /** Present when rows were merged from more than one MCP run. */
  collectedFrom?: string
  collectedTo?: string
  store: { code: string; name: string; city: string; businessStatus?: boolean | null }
  /** Machine-readable channel; merges are only allowed within one channel. */
  channel?: { orderType: number; beType: number }
  orderType: string
  toolsUsed: string[]
  notes: string
  items: SnapshotItem[]
}

/**
 * The menu is daypart-dependent (breakfast carries no burgers), so one run
 * cannot always see all eight seeds. When the snapshot merges several runs,
 * showing the newest stamp alone would overstate how fresh most rows are.
 */
export function collectedLabel(s: Snapshot): string {
  const tz = s.collectedAtTimezone ? ` ${s.collectedAtTimezone}` : ''
  if (s.collectedFrom && s.collectedTo && s.collectedFrom !== s.collectedTo) {
    return `${s.collectedFrom} ~ ${s.collectedTo}${tz}（分批采集）`
  }
  return `${s.collectedAt}${tz}`
}

/** The price we display, with an explicit provenance. */
export function effectivePriceCents(item: SnapshotItem): number | null {
  return item.quotePriceCents ?? item.menuPriceCents
}

/**
 * Where the displayed price came from. An item without a successful
 * calculate-price run is shown as a menu reference price — never dressed
 * up as a verified quote.
 */
export function priceSourceLabel(item: SnapshotItem): string {
  if (item.quotePriceCents !== null) return '官方核价'
  if (item.menuPriceCents !== null) return '菜单参考价'
  return '暂无可靠数据'
}

/** Price plus provenance, e.g. "¥25.5 · 官方核价". */
export function priceCaption(item: SnapshotItem): string {
  const kind = priceSourceLabel(item)
  if (kind === '暂无可靠数据') return kind
  return `${formatYuan(effectivePriceCents(item))} · ${kind}`
}

/** "2026-10-15 22:00:51" -> "10-15 22:00". */
export function formatStamp(stamp?: string | null): string {
  if (!stamp) return '时间未知'
  const m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}:\d{2})/.exec(stamp)
  return m ? `${m[2]}-${m[3]} ${m[4]}` : stamp
}

/** When this item's price evidence was captured (a quote may be older). */
export function priceStamp(item: SnapshotItem): string {
  return formatStamp(item.quoteCollectedAt ?? item.collectedAt)
}

export function formatYuan(cents: number | null): string {
  if (cents === null) return '暂无可靠数据'
  // 25.50 -> 25.5, 7.00 -> 7 — money should not look padded.
  const s = (cents / 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
  return `¥${s}`
}

/** A nutrient value, or an em dash when the official table has no value. */
export function formatMetric(value: number | null, unit: string): string {
  return value === null ? '—' : `${value}${unit}`
}
