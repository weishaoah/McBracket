export interface Nutrition {
  energyKcal: number
  protein: number
  fat: number
  carbohydrate: number
  sodium: number
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
  /** Category tag used only for labelling; never used to invent data. */
  category?: string
}

export interface Snapshot {
  schema: string
  mode: 'demo-snapshot' | 'live'
  endpoint: string
  collectedAt: string
  collectedAtTimezone: string
  store: { code: string; name: string; city: string; businessStatus?: boolean | null }
  orderType: string
  toolsUsed: string[]
  notes: string
  items: SnapshotItem[]
}

/** The price we display, with an explicit provenance. */
export function effectivePriceCents(item: SnapshotItem): number | null {
  return item.quotePriceCents ?? item.menuPriceCents
}

export function formatYuan(cents: number | null): string {
  if (cents === null) return '暂无可靠数据'
  // 25.50 -> 25.5, 7.00 -> 7 — money should not look padded.
  const s = (cents / 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
  return `¥${s}`
}
