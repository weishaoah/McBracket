import type { SnapshotItem } from '../types'
import { effectivePriceCents, formatYuan } from '../types'

/**
 * Original, tongue-in-cheek titles derived only from things that are actually
 * true: the champion's own numbers, its rank among the eight contenders, and
 * who it beat. Nothing here infers anything about the person playing.
 */

export interface ChampionFlair {
  badge: string
  quote: string
  facts: string[]
}

function rank(values: Array<number | null>, target: number | null): number | null {
  if (target === null) return null
  const sorted = values.filter((v): v is number => v !== null).sort((a, b) => b - a)
  const i = sorted.indexOf(target)
  return i < 0 ? null : i + 1
}

export function championFlair(
  champion: SnapshotItem,
  field: SnapshotItem[],
  eliminated: SnapshotItem[],
  finalOpponent: SnapshotItem | null,
): ChampionFlair {
  const prices = field.map(effectivePriceCents)
  const kcals = field.map((i) => i.nutrition?.energyKcal ?? null)
  const proteins = field.map((i) => i.nutrition?.protein ?? null)
  const sodiums = field.map((i) => i.nutrition?.sodium ?? null)

  const cPrice = effectivePriceCents(champion)
  const cKcal = champion.nutrition?.energyKcal ?? null
  const cProtein = champion.nutrition?.protein ?? null
  const cSodium = champion.nutrition?.sodium ?? null

  const priceRank = rank(prices, cPrice)
  const kcalRank = rank(kcals, cKcal)
  const proteinRank = rank(proteins, cProtein)
  const sodiumRank = rank(sodiums, cSodium)

  const facts: string[] = []
  if (cPrice !== null && priceRank) facts.push(`价格全场第 ${priceRank} 高`)
  if (cKcal !== null && kcalRank) facts.push(`热量全场第 ${kcalRank} 高`)
  if (cProtein !== null && proteinRank === 1) facts.push('蛋白质全场第一')
  if (cSodium !== null && sodiumRank === 1) facts.push('钠含量全场第一')

  // Cheapest half of the field, or beat something notably pricier.
  const elimPrices = eliminated.map(effectivePriceCents).filter((v): v is number => v !== null)
  const avgElim = elimPrices.length
    ? elimPrices.reduce((a, b) => a + b, 0) / elimPrices.length
    : null

  let badge = '麦门无冕之王'
  let quote = '七场厮杀之后，它站在了麦门之巅。'

  if (kcalRank === 1) {
    badge = '热量核弹'
    quote = '你选的不是一份餐，是一整座能量反应堆。'
  } else if (proteinRank === 1) {
    badge = '蛋白狂人'
    quote = '增肌党看到这个结果，大概会默默点头。'
  } else if (cPrice !== null && avgElim !== null && cPrice < avgElim * 0.8) {
    badge = '性价比之王'
    quote = '便宜不是缺点，是你眼光好的证据。'
  } else if (kcalRank !== null && kcals.filter(Boolean).length >= 4 && kcalRank === kcals.filter((v) => v !== null).length) {
    badge = '轻盈派代表'
    quote = '在热量军备竞赛里，你投了克制一票。'
  } else if (sodiumRank === 1) {
    badge = '钠量担当'
    quote = '重口味的胜利，明天的水记得多喝两杯。'
  } else if (priceRank === 1) {
    badge = '贵气逼人'
    quote = '你用钱包投票，选了全场最贵的那位。'
  }

  if (finalOpponent) {
    const oPrice = effectivePriceCents(finalOpponent)
    if (cPrice !== null && oPrice !== null && oPrice > cPrice * 1.25 && badge === '性价比之王') {
      quote = `决赛亲手送走了更贵的${finalOpponent.name}，省下的钱够再来一份。`
    }
  }

  return { badge, quote, facts }
}

export function priceLabel(item: SnapshotItem): string {
  return formatYuan(effectivePriceCents(item))
}
