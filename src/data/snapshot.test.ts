import { describe, expect, it } from 'vitest'
import snapshotJson from './snapshot.json'
import { ART_BY_CODE } from './art'
import {
  collectedLabel,
  effectivePriceCents,
  formatMetric,
  formatStamp,
  formatYuan,
  priceCaption,
  priceSourceLabel,
  type Snapshot,
  type SnapshotItem,
} from '../types'

const snapshot = snapshotJson as unknown as Snapshot
const items = snapshot.items

/**
 * These are the values the official nutrition table returned on
 * 2026-10-15 (official now-time-info clock, via list-nutrition-foods).
 * They are pinned on purpose: if a future refresh changes them, this test
 * fails and the numbers must be updated deliberately — nobody can quietly
 * hand-edit a calorie count into the demo.
 */
const OFFICIAL_NUTRITION: Record<string, SnapshotItem['nutrition']> = {
  1100: { energyKcal: 513, protein: 27, fat: 26, carbohydrate: 42, sodium: 961 },
  511781: { energyKcal: 707, protein: 34, fat: 44, carbohydrate: 43, sodium: 1037 },
  4648: { energyKcal: 493, protein: 28, fat: 27, carbohydrate: 34, sodium: 1012 },
  1600: { energyKcal: 325, protein: 16, fat: 13, carbohydrate: 35, sodium: 556 },
  1450: { energyKcal: 369, protein: 15, fat: 17, carbohydrate: 39, sodium: 731 },
  520445: { energyKcal: 192, protein: 17, fat: 11, carbohydrate: 6, sodium: 594 },
  2430: { energyKcal: 165, protein: 0, fat: 0, carbohydrate: 41, sodium: 53 },
  6102: { energyKcal: 32, protein: 0, fat: 0, carbohydrate: 7, sodium: 0 },
}

describe('snapshot integrity', () => {
  it('carries exactly eight distinct contenders', () => {
    expect(items).toHaveLength(8)
    expect(new Set(items.map((i) => i.code)).size).toBe(8)
  })

  it('has an illustration for every contender', () => {
    for (const it of items) {
      expect(ART_BY_CODE[it.code], `no art for ${it.code}`).toBeDefined()
    }
  })

  it('names every contender', () => {
    for (const it of items) {
      expect(it.name.length).toBeGreaterThan(0)
    }
  })

  it('never shows a price it cannot source', () => {
    for (const it of items) {
      if (it.priceSource === 'calculate-price') {
        expect(it.quotePriceCents, it.code).not.toBeNull()
      }
      if (it.priceSource === 'query-meals') {
        expect(it.menuPriceCents, it.code).not.toBeNull()
        expect(it.quotePriceCents, it.code).toBeNull()
      }
      expect(effectivePriceCents(it), it.code).not.toBeNull()
    }
  });

  it('shows the quote only when it agrees with the menu price', () => {
    for (const it of items) {
      if (it.quotePriceCents !== null && it.menuPriceCents !== null) {
        expect(it.quotePriceCents, it.code).toBe(it.menuPriceCents)
      }
    }
  })

  it('pins the official nutrition values', () => {
    for (const it of items) {
      expect(it.nutritionMatch, it.code).toBe('exact')
      expect(it.nutrition, it.code).toEqual(OFFICIAL_NUTRITION[it.code])
    }
  })

  it('labels itself as a snapshot, not a live query', () => {
    expect(snapshot.mode).toBe('demo-snapshot')
    expect(snapshot.capturedWith).toBe('official-mcp')
  })

  it('keeps a per-row capture timestamp inside the reported window', () => {
    const newest = snapshot.collectedTo ?? snapshot.collectedAt
    for (const it of items) {
      expect(it.collectedAt, it.code).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)
      expect(it.collectedAt! <= newest, it.code).toBe(true)
    }
    // A carried row is one the latest run did not see on the menu, so its
    // stamp must be strictly older than the newest row in the file.
    for (const it of items.filter((i) => i.carried)) {
      expect(it.collectedAt! < newest, it.code).toBe(true)
    }
  })
})

describe('price display', () => {
  const quoted: SnapshotItem = { ...items[0], quotePriceCents: 2550, menuPriceCents: 2550, priceSource: 'calculate-price' }
  const menuOnly: SnapshotItem = { ...items[0], quotePriceCents: null, menuPriceCents: 3450, priceSource: 'query-meals' }
  const priceless: SnapshotItem = { ...items[0], quotePriceCents: null, menuPriceCents: null, priceSource: 'none' }

  it('labels a verified quote as 官方核价', () => {
    expect(priceSourceLabel(quoted)).toBe('官方核价')
    expect(priceCaption(quoted)).toBe('¥25.5 · 官方核价')
  })

  it('labels an unverified item as 菜单参考价', () => {
    expect(priceSourceLabel(menuOnly)).toBe('菜单参考价')
    expect(priceCaption(menuOnly)).toBe('¥34.5 · 菜单参考价')
  })

  it('never invents a price', () => {
    expect(priceSourceLabel(priceless)).toBe('暂无可靠数据')
    expect(priceCaption(priceless)).toBe('暂无可靠数据')
    expect(formatYuan(null)).toBe('暂无可靠数据')
  })
})

describe('formatting', () => {
  it('renders cents as unpadded yuan', () => {
    expect(formatYuan(2550)).toBe('¥25.5')
    expect(formatYuan(700)).toBe('¥7')
    expect(formatYuan(1300)).toBe('¥13')
  })

  it('renders a missing nutrient as an em dash, not a zero', () => {
    expect(formatMetric(null, ' mg')).toBe('—')
    expect(formatMetric(961, ' mg')).toBe('961 mg')
  })

  it('renders official timestamps compactly', () => {
    expect(formatStamp('2026-10-15 22:00:51')).toBe('10-15 22:00')
    expect(formatStamp('2026-10-14 11:26:56')).toBe('10-14 11:26')
    expect(formatStamp(null)).toBe('时间未知')
    expect(formatStamp('not-a-stamp')).toBe('not-a-stamp')
  })

  it('shows a capture window when rows come from several runs', () => {
    expect(collectedLabel(snapshot)).toContain('~')
    const single = { ...snapshot, collectedFrom: undefined, collectedTo: undefined }
    expect(collectedLabel(single)).toBe(`${snapshot.collectedAt} ${snapshot.collectedAtTimezone}`)
  })
})
