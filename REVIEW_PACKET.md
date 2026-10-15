# McBracket · 外部审查包

> 自包含审查材料：项目背景 + 数据证据 + 全部源码 + 待审问题。
> 重新生成：`python scripts/make_review_packet.py`（代码改了记得重跑）。

### 怎么用

1. **整篇复制粘贴**给 GPT / Claude 等外部模型（约 65KB，长上下文模型无压力）。
2. 粘贴时**不要删 §0 的审查指令** —— 那段决定了它审什么；只丢源码进去，模型会退化成「夸一遍代码写得不错」。
3. 若上下文实在不够，优先级：`§0 指令` → `§2 数据证据` → `§5 源码里的 types.ts / tournament.ts / fetch_snapshot.py`。
4. **拿到回复后**：重点看它挑出的「说了但没做到」和「证据不足」，这两类问题我自己看不见。它夸的部分基本可以忽略。

**审查目的**：我（作者）已在这个项目上投入大量上下文，存在明显盲区，
需要外部视角找出**我说错、夸大或证据不足**的地方。
**不需要客套，请直接指出问题。**

---

## 0. 给审查者的指令

请按下列顺序审，并**明确指出我说错或夸大的地方**（这是我找外部审查的唯一目的，
不需要为了照顾我而保留情面）：

### A. 数据真实性（最高优先级 —— 比赛会查）
1. `fetch_snapshot.py` 与 `snapshot.json` 里，有没有任何一处会让读者误以为
   当前页面数据是**实时**的？我已经修过 `mode` 字段（改成 `demo-snapshot`，
   页面显示「非实时」）和分批采集的时间区间，但可能还有漏网的措辞。
2. 「菜单价（元·字符串）vs 核价（分·整数）」的换算是否真的正确？
   请独立核一遍 `yuan_to_cents()` 和 `effectivePriceCents()`，
   这是本项目最容易出错、也最容易被评委一眼看穿的地方。
3. 营养数据只取「商品名精确匹配」，其余显示「暂无可靠数据」。
   这个降级策略有没有在某处被绕过（比如悄悄填了 0 或估算值）？

### B. 合规风险（会不会被取消资格或收到律师函）
4. 项目名含 "Mc"，README 与冠军卡上出现麦当劳商品名。
   以你的判断，这构成商标风险吗？声明「独立作品、非官方出品」的位置
   是否足够显眼？
5. `CONTEST_DECLARATION.md` 要求与官方模板逐字节一致，我已核对
   （md5 `91a7b32e`）。还有哪些参赛材料是容易被漏掉的形式要求？

### C. 代码正确性
6. `tournament.ts` 的晋级逻辑：有没有可能出现同一商品重复晋级、
   某场比赛被跳过、或 7 场没跑完就出冠军？（我有 11 条测试含 200 次随机对局，
   但测试可能有盲区 —— 请特别看测试**没有覆盖**的分支。）
7. `merge_items()` 的合并逻辑：分批采集时会不会错误地用旧数据覆盖新数据？
   `_score()` 的排序是否存在某种情况下会退化？
8. 有没有任何路径会执行写入类 Tool（下单/领券/抽奖）？

### D. 竞争力（这是比赛，排名只看 GitHub Star）
9. 以评审者/路人的视角：**这个 README 前三屏**能不能让人想点 Star？
   最劝退的地方在哪？
10. 项目最大的卖点应该是什么？我现在的说法
    （「真实 MCP 数据 + 8 强淘汰赛 + 可分享冠军卡」）是不是太平淡？
11. 有没有明显的「自嗨」痕迹 —— 即我觉得有价值、但外人根本不关心的部分？

### E. 诚实性审查（最重要）
12. 通读 `MCP_INTEGRATION.md` 与 `README.md`，
    找出所有**证据不足以支撑**的断言。我已经知道的一个自我质疑是：
    「8 强选择理由是价格带宽 + 品类分散」，但实际上有 6/8 没有官方核价验证。
    请把这类「说了但其实没做到」的地方都挑出来。

---

## 1. 项目是什么

McBracket 是一个参加「麦当劳中国开发者创新挑战赛」的网页小游戏：
从 8 款**真实**麦当劳餐品中，通过 7 场一对一对决（8进4→4进2→决赛），
选出用户最喜欢的餐品，生成可分享的冠军卡 PNG。

比赛排名**只看 GitHub Star 数**（截止 2026-10-25），所以「能不能让人
想点 Star」和「数据是否真实」同等重要。

技术栈：React + TypeScript + Vite，纯前端，无后端、无数据库、无登录。
数据来自麦当劳官方 MCP（`https://mcp.mcd.cn`）的**只读**采集快照。

## 2. 数据证据（请逐条核）

- 门店：**麦当劳上海黄浦华旭国际大厦餐厅**（1450713）
- 渠道：堂食/到店取餐渠道（orderType=1, beType=1）
- 采集时间：2026-10-14 11:26:56 ~ 2026-10-15 09:56:44 GMT+08:00
- `mode`：`demo-snapshot`　`capturedWith`：`official-mcp`
- 使用的 Tool：calculate-price, list-nutrition-foods, now-time-info, query-meals, query-nearby-stores
- **核价验证覆盖：2/8**（上次运行新采 1 条、沿用 7 条）

| code | 商品 | 菜单价 | 官方核价 | 价格来源 | 热量 | 采集时间 |
|---|---|---:|---:|---|---:|---|
| 1100 | 巨无霸 | ¥25.5 | ¥25.5 ✓一致 | calculate-price | 513 | 2026-10-14 11:26:56 |
| 511781 | 培根安格斯厚牛堡 | ¥34.5 | - | query-meals | 707 | 2026-10-14 11:26:56 |
| 4648 | 不素之霸双层牛堡 | ¥26.5 | - | query-meals | 493 | 2026-10-14 11:26:56 |
| 1600 | 麦香鱼 | ¥22.5 | - | query-meals | 325 | 2026-10-14 11:26:56 |
| 1450 | 麦香鸡 | ¥17 | - | query-meals | 369 | 2026-10-14 11:26:56 |
| 520445 | 薄皮焦香V翅 | ¥16 | - | query-meals | 192 | 2026-10-14 11:26:56 |
| 2430 | 【美汁源】“黄金橙橙” | ¥13 | ¥13 ✓一致 | calculate-price | 165 | 2026-10-15 09:56:44 |
| 6102 | 苹果片 | ¥7 | - | query-meals | 32 | 2026-10-14 11:26:56 |

## 3. 已知问题（作者自述）

### 我自己已经知道的问题（不用重复指出，但欢迎说它比我想的更严重）

1. **核价只验证 2/8**：只有巨无霸（¥25.5）和美汁源（¥13.0）拿到了
   `calculate-price` 官方核价，其余 6 款降级为 `query-meals` 菜单价。
   原因是麦当劳菜单按营业时段切换，早餐时段汉堡不在菜单里。
   计划午间正餐时段重采补齐。
2. **Demo 模式就是唯一模式**：页面始终读静态快照，没有真正的实时路径。
   「模式 B（真实 MCP）」目前只是「开发者本地重新生成快照」，
   措辞上我尽量说清楚了，但这不是真正的双模式。
3. **单门店单渠道**：全部数据来自上海一家门店（1450713）、
   orderType=1/beType=1。换城市/门店的差异完全没有被覆盖。
4. **`query-meal-detail` 脚本支持但页面未使用**：集成文档里列了它，
   但游戏里没用到，属于「说了但没做」。
5. **营养表只覆盖常驻单品**：套餐和限定品一律「暂无可靠数据」，
   8 强能全部精确匹配是因为我**特意挑**了能匹配的 8 款
   —— 这有选择性偏差，不是随机抽样。

## 4. 项目元数据

```
git log: 486df42 Stop the snapshot from lying about freshness, coverage and liveness
00e7745 McBracket: pick your McDonald's champion through 7 real-data duels
status : M scripts/fetch_snapshot.py
 M src/data/snapshot.json
?? REVIEW_PACKET.md
?? scripts/make_review_packet.py
```

## 5. 源码

### `src/types.ts`

```ts
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
  /** Present when rows were merged from more than one MCP run. */
  collectedFrom?: string
  collectedTo?: string
  store: { code: string; name: string; city: string; businessStatus?: boolean | null }
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

export function formatYuan(cents: number | null): string {
  if (cents === null) return '暂无可靠数据'
  // 25.50 -> 25.5, 7.00 -> 7 — money should not look padded.
  const s = (cents / 100).toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
  return `¥${s}`
}

```

### `src/engine/tournament.ts`

```ts
/**
 * Pure tournament logic. No React, no DOM, no MCP — so the rules that decide
 * who advances can be tested without a browser.
 *
 * Layout is a fixed single-elimination bracket:
 *   M0 QF  seed0 vs seed1 ┐
 *   M1 QF  seed2 vs seed3 ┴ M4 SF ┐
 *   M2 QF  seed4 vs seed5 ┐       ├ M6 FINAL
 *   M3 QF  seed6 vs seed7 ┴ M5 SF ┘
 */

export type Round = 'QF' | 'SF' | 'F'

export const ROUND_LABEL: Record<Round, string> = {
  QF: '四分之一决赛',
  SF: '半决赛',
  F: '总决赛',
}

export const TOTAL_MATCHES = 7

export interface Match {
  index: number
  round: Round
  slotA: string | null
  slotB: string | null
}

export interface ResolvedMatch extends Match {
  slotA: string
  slotB: string
}

/** Deterministic PRNG so a "restart" can reshuffle reproducibly in tests. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

export function shuffle<T>(input: readonly T[], rand: () => number = Math.random): T[] {
  const out = input.slice()
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

/**
 * Seven match slots. Later rounds start empty and are filled by
 * {@link resolve} as picks come in — nothing is fabricated ahead of time.
 */
export function buildMatches(seeds: readonly string[]): Match[] {
  if (seeds.length !== 8) throw new Error(`bracket needs exactly 8 seeds, got ${seeds.length}`)
  const m = (index: number, round: Round, a: string | null, b: string | null): Match => ({
    index,
    round,
    slotA: a,
    slotB: b,
  })
  return [
    m(0, 'QF', seeds[0], seeds[1]),
    m(1, 'QF', seeds[2], seeds[3]),
    m(2, 'QF', seeds[4], seeds[5]),
    m(3, 'QF', seeds[6], seeds[7]),
    m(4, 'SF', null, null),
    m(5, 'SF', null, null),
    m(6, 'F', null, null),
  ]
}

/** Fill later-round slots from recorded winners. */
export function resolve(matches: readonly Match[], picks: readonly (string | null)[]): Match[] {
  const out = matches.map((m) => ({ ...m }))
  const feed: Array<[number, number, number]> = [
    // [target match, winner of match X, winner of match Y]
    [4, 0, 1],
    [5, 2, 3],
    [6, 4, 5],
  ]
  for (const [target, ax, bx] of feed) {
    out[target].slotA = picks[ax] ?? null
    out[target].slotB = picks[bx] ?? null
  }
  return out
}

/** First match that has both contenders known and no winner yet, else null. */
export function currentMatchIndex(
  matches: readonly Match[],
  picks: readonly (string | null)[],
): number | null {
  for (const m of matches) {
    if (m.slotA && m.slotB && !picks[m.index]) return m.index
  }
  return null
}

export function championCode(picks: readonly (string | null)[]): string | null {
  return picks[picks.length - 1] ?? null
}

/** Every contender that lost a completed match, most recent last. */
export function eliminatedCodes(
  matches: readonly Match[],
  picks: readonly (string | null)[],
): string[] {
  const out: string[] = []
  for (const m of matches) {
    const winner = picks[m.index]
    if (!winner || !m.slotA || !m.slotB) continue
    out.push(m.slotA === winner ? m.slotB : m.slotA)
  }
  return out
}

/** Champion's opponents, round by round — the "route" shown on the result page. */
export function championRoute(
  matches: readonly Match[],
  champion: string,
): Array<{ round: Round; opponent: string }> {
  return matches
    .filter((m) => m.slotA && m.slotB && (m.slotA === champion || m.slotB === champion))
    .map((m) => ({
      round: m.round,
      opponent: m.slotA === champion ? (m.slotB as string) : (m.slotA as string),
    }))
}

/** Counted from the picks themselves so it is correct for unresolved brackets too. */
export function roundProgress(_matches: readonly Match[], picks: readonly (string | null)[]): {
  done: number
  total: number
} {
  return { done: picks.filter(Boolean).length, total: TOTAL_MATCHES }
}

```

### `src/engine/championTitle.ts`

```ts
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

```

### `src/App.tsx`

```ts
import { useCallback, useMemo, useRef, useState } from 'react'
import snapshotJson from './data/snapshot.json'
import { collectedLabel, type Snapshot, type SnapshotItem } from './types'
import {
  buildMatches,
  championCode,
  championRoute,
  eliminatedCodes,
  resolve,
  roundProgress,
  shuffle,
} from './engine/tournament'
import { championFlair } from './engine/championTitle'
import { HomeView } from './components/HomeView'
import { MatchView } from './components/MatchView'
import { BracketView } from './components/BracketView'
import { ChampionCard } from './components/ChampionCard'
import { FoodArt } from './components/FoodArt'

const snapshot = snapshotJson as Snapshot
const ITEMS: SnapshotItem[] = snapshot.items
const BY_CODE = new Map(ITEMS.map((i) => [i.code, i]))
const REPO_URL = 'https://github.com/weishaoah/McBracket'

type Stage = 'home' | 'playing' | 'champion'

export default function App() {
  const [stage, setStage] = useState<Stage>('home')
  const [order, setOrder] = useState<string[]>(() => ITEMS.map((i) => i.code))
  const [picks, setPicks] = useState<Array<string | null>>(() => Array(7).fill(null))
  /** Which match is on screen; the reveal keeps it visible until 「下一场」. */
  const [viewIndex, setViewIndex] = useState(0)
  const [busy, setBusy] = useState<string | null>(null)
  const cardRef = useRef<HTMLDivElement>(null)

  const matches = useMemo(() => resolve(buildMatches(order), picks), [order, picks])
  const { done } = roundProgress(matches, picks)
  const champion = championCode(picks)

  const start = useCallback(() => {
    setOrder(shuffle(ITEMS.map((i) => i.code)))
    setPicks(Array(7).fill(null))
    setViewIndex(0)
    setStage('playing')
  }, [])

  const pick = useCallback(
    (code: string) => {
      setPicks((prev) => {
        if (prev[viewIndex] !== null) return prev
        const next = prev.slice()
        next[viewIndex] = code
        return next
      })
    },
    [viewIndex],
  )

  const next = useCallback(() => {
    if (viewIndex === 6) setStage('champion')
    else setViewIndex((v) => Math.min(v + 1, 6))
  }, [viewIndex])

  const nameOf = useCallback(
    (code: string | null) => (code ? BY_CODE.get(code)?.name ?? code : '待定'),
    [],
  )

  const exportPng = useCallback(async (kind: 'card') => {
    const node = cardRef.current
    if (!node) return
    setBusy(kind)
    try {
      const { toPng } = await import('html-to-image')
      const dataUrl = await toPng(node, { pixelRatio: 2, backgroundColor: '#120e0c' })
      // Blob URL: data URLs do not trigger a download event in headless browsers.
      const blob = await (await fetch(dataUrl)).blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.download = `mcbracket-${kind}-${Date.now()}.png`
      link.href = url
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 8000)
    } catch (err) {
      console.error('export failed', err)
      alert('导出失败，请重试（部分浏览器会阻止自动下载）。')
    } finally {
      setBusy(null)
    }
  }, [])

  // Dev-only hook: lets automated browser tests drive the exporter and check
  // that a real PNG is produced. Stripped from production builds.
  if (import.meta.env.DEV) {
    ;(window as unknown as Record<string, unknown>).__mcbracketDebug = {
      exportPng,
      pngLength: async () => {
        const node = cardRef.current
        if (!node) return -1
        const { toPng } = await import('html-to-image')
        const d = await toPng(node, { pixelRatio: 2, backgroundColor: '#120e0c' })
        return d.length
      },
    }
  }

  const flair = useMemo(() => {    if (!champion) return null
    const c = BY_CODE.get(champion)!
    const eliminated = eliminatedCodes(matches, picks)
      .map((code) => BY_CODE.get(code))
      .filter((i): i is SnapshotItem => Boolean(i))
    const finalMatch = matches[6]
    const oppCode =
      finalMatch.slotA === champion ? finalMatch.slotB : finalMatch.slotA
    return championFlair(c, ITEMS, eliminated, oppCode ? BY_CODE.get(oppCode) ?? null : null)
  }, [champion, matches, picks])

  const route = useMemo(
    () => (champion ? championRoute(matches, champion) : []),
    [champion, matches],
  )
  const eliminated = useMemo(
    () => eliminatedCodes(matches, picks),
    [matches, picks],
  )

  return (
    <div className="app">
      <div className="topbar">
        <div className="brand">
          <span className="brand-mark">McBracket</span>
          <span className="brand-sub">麦门最强餐品争霸赛</span>
        </div>
        <div className="pill">
          <span className="pill-dot" />
          {snapshot.mode === 'demo-snapshot' ? '官方数据快照' : '实时 MCP'}
        </div>
      </div>

      {stage === 'home' && (
        <HomeView snapshot={snapshot} items={ITEMS} onStart={start} />
      )}

      {stage === 'playing' && matches[viewIndex].slotA && matches[viewIndex].slotB && (
        <MatchView
          match={matches[viewIndex]}
          a={BY_CODE.get(matches[viewIndex].slotA!)!}
          b={BY_CODE.get(matches[viewIndex].slotB!)!}
          done={done}
          pick={picks[viewIndex]}
          byCode={BY_CODE}
          onPick={pick}
          onNext={next}
          isLast={viewIndex === 6}
        />
      )}

      {stage === 'champion' && champion && flair && (
        <div className="champion">
          <div className="champion-crown">👑</div>
          <div className="champion-title">我 的 麦 门 冠 军</div>
          <h2 className="champion-name" data-testid="champion-name">
            {BY_CODE.get(champion)!.name}
          </h2>
          <FoodArt code={champion} size={150} className="champion-art" />
          <div className="champion-badge">{flair.badge}</div>

          <div className="section">
            <div className="section-title">晋 级 路 线</div>
            <div className="route">
              {route.map((r, i) => (
                <div className="route-item" key={i}>
                  <span className="route-round">{r.round === 'QF' ? '8 进 4' : r.round === 'SF' ? '4 进 2' : '总决赛'}</span>
                  <span className="route-beat">击败</span>
                  <span className="route-opponent">{nameOf(r.opponent)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="section">
            <div className="section-title">被 你 淘 汰 的 七 位</div>
            <div className="chips">
              {eliminated.map((code, i) => (
                <span className="chip" key={`${code}-${i}`}>
                  {nameOf(code)}
                </span>
              ))}
            </div>
          </div>

          <div className="section">
            <div className="section-title">完 整 对 阵 图</div>
            <BracketView matches={matches} picks={picks} nameOf={nameOf} />
          </div>

          <div className="btn-row">
            <button
              className="btn btn-amber"
              onClick={() => exportPng('card')}
              disabled={busy !== null}
              data-testid="export"
            >
              {busy === 'card' ? '生成中…' : '保存冠军卡 PNG'}
            </button>
            <button className="btn btn-ghost" onClick={start} data-testid="restart">
              重新挑战
            </button>
          </div>

          <div className="source">
            <div>
              <b>数据来源</b>：麦当劳官方 MCP（{snapshot.toolsUsed.join('、')}）
            </div>
            <div>
              <b>采集门店</b>：{snapshot.store.name}（{snapshot.store.code}）· {snapshot.orderType}
            </div>
            <div>
              <b>采集时间</b>：{collectedLabel(snapshot)}
              {snapshot.mode === 'demo-snapshot' ? '（官方数据快照，非实时）' : '（实时查询）'}
            </div>
            <div>
              冠军称号为原创趣味文案，仅依据上表的真实数据与赛果生成，不代表任何性格或偏好判断。
              本作品为独立开发项目，与麦当劳官方无关。
            </div>
          </div>
        </div>
      )}

      {stage === 'champion' && champion && flair && (
        <div className="export-stage" aria-hidden>
          <div ref={cardRef}>
            <ChampionCard
              snapshot={snapshot}
              champion={BY_CODE.get(champion)!}
              badge={flair.badge}
              quote={flair.quote}
              route={route.map((r) => ({ ...r, opponent: nameOf(r.opponent) }))}
              repoUrl={REPO_URL}
            />
          </div>
        </div>
      )}
    </div>
  )
}

```

### `src/components/MatchView.tsx`

```ts
import { FoodArt } from './FoodArt'
import { DataReveal } from './DataReveal'
import { priceLabel } from '../engine/championTitle'
import { ROUND_LABEL, TOTAL_MATCHES, type Match } from '../engine/tournament'
import type { SnapshotItem } from '../types'

interface Props {
  match: Match
  a: SnapshotItem
  b: SnapshotItem
  done: number
  pick: string | null
  byCode: Map<string, SnapshotItem>
  onPick: (code: string) => void
  onNext: () => void
  isLast: boolean
}

export function MatchView({ match, a, b, done, pick, byCode, onPick, onNext, isLast }: Props) {
  const locked = pick !== null
  const label = ROUND_LABEL[match.round]

  const card = (item: SnapshotItem, side: 'a' | 'b') => {
    const isWinner = pick === item.code
    const isLoser = locked && !isWinner
    return (
      <button
        key={item.code}
        className={`contender${isWinner ? ' win' : ''}${isLoser ? ' lose' : ''}${
          locked ? ' locked' : ''
        }`}
        disabled={locked}
        onClick={() => onPick(item.code)}
        data-testid={`pick-${side}`}
        aria-label={`选择 ${item.name}`}
      >
        <FoodArt code={item.code} size={104} />
        <div className="contender-name">{item.name}</div>
        <div className="contender-meta">{priceLabel(item)}</div>
        <div className="contender-hint">
          {locked ? (isWinner ? '晋级 ✓' : '淘汰') : '点我晋级'}
        </div>
      </button>
    )
  }

  return (
    <div>
      <div className="progress">
        <div className="bar">
          <div className="bar-fill" style={{ width: `${(done / TOTAL_MATCHES) * 100}%` }} />
        </div>
        <div className="progress-text" data-testid="progress">
          第 {Math.min(done + 1, TOTAL_MATCHES)} 场 / 共 {TOTAL_MATCHES} 场
        </div>
      </div>

      <div className="round-tag">{label}</div>

      <div className="arena">
        {card(a, 'a')}
        <div className="vs">VS</div>
        {card(b, 'b')}
      </div>

      {locked && (
        <DataReveal
          a={byCode.get(pick!)!}
          b={pick === a.code ? b : a}
          onNext={onNext}
          isLast={isLast}
        />
      )}
    </div>
  )
}

```

### `src/components/DataReveal.tsx`

```ts
import { effectivePriceCents, formatYuan, type SnapshotItem } from '../types'

interface Props {
  a: SnapshotItem
  b: SnapshotItem
  onNext: () => void
  isLast: boolean
}

interface Row {
  label: string
  unit: string
  av: number | null
  bv: number | null
  fmt?: (v: number) => string
}

function Row({ row }: { row: Row }) {
  const { av, bv, unit, label } = row
  const fmt = row.fmt ?? ((v: number) => String(v))
  if (av === null || bv === null) {
    return (
      <div className="reveal-row">
        <div className="val a lower">暂无可靠数据</div>
        <div className="lbl">{label}</div>
        <div className="val b lower">暂无可靠数据</div>
      </div>
    )
  }
  return (
    <div className="reveal-row">
      <div className={`val a ${av > bv ? 'higher' : av < bv ? 'lower' : ''}`}>
        {fmt(av)}
        {unit}
      </div>
      <div className="lbl">{label}</div>
      <div className={`val b ${bv > av ? 'higher' : bv < av ? 'lower' : ''}`}>
        {fmt(bv)}
        {unit}
      </div>
    </div>
  )
}

export function DataReveal({ a, b, onNext, isLast }: Props) {
  const rows: Row[] = [
    { label: '价格', unit: '', av: effectivePriceCents(a), bv: effectivePriceCents(b), fmt: formatYuan },
    { label: '热量', unit: ' kcal', av: a.nutrition?.energyKcal ?? null, bv: b.nutrition?.energyKcal ?? null },
    { label: '蛋白质', unit: ' g', av: a.nutrition?.protein ?? null, bv: b.nutrition?.protein ?? null },
    { label: '钠', unit: ' mg', av: a.nutrition?.sodium ?? null, bv: b.nutrition?.sodium ?? null },
  ]

  const missing =
    rows[0].av === null ||
    rows[0].bv === null ||
    a.nutritionMatch === 'none' ||
    b.nutritionMatch === 'none'

  return (
    <div className="reveal" data-testid="reveal">
      <div className="reveal-title">
        数 据 揭 晓 · {a.name} 晋级
      </div>
      {rows.map((r) => (
        <Row key={r.label} row={r} />
      ))}
      <div className="reveal-note">
        以上为同一门店、同一订餐渠道下的官方数据对比；价格优先采用官方核价接口结果，
        菜单价与核价单位不同（元 / 分），已统一换算后比较。
        {missing && ' 部分商品缺少可精确匹配的官方数据，已如实标注，未作推测。'}
      </div>
      <div className="next-row">
        <button className="btn btn-primary" onClick={onNext} data-testid="next">
          {isLast ? '查看我的麦门冠军' : '下一场 →'}
        </button>
      </div>
    </div>
  )
}

```

### `src/components/ChampionCard.tsx`

```ts
import { FoodArt } from './FoodArt'
import { priceLabel } from '../engine/championTitle'
import { ROUND_LABEL, type Round } from '../engine/tournament'
import { collectedLabel, type Snapshot, type SnapshotItem } from '../types'

interface Props {
  snapshot: Snapshot
  champion: SnapshotItem
  badge: string
  quote: string
  route: Array<{ round: Round; opponent: string }>
  repoUrl: string
}

/**
 * Fixed 750px-wide layout rendered offscreen and rasterised to PNG.
 * Width is fixed so Chinese text wraps exactly the same way on every device.
 */
export function ChampionCard({ snapshot, champion, badge, quote, route, repoUrl }: Props) {
  return (
    <div className="card-export">
      <div className="card-head">
        <div className="card-brand">McBracket</div>
        <div className="card-brand-cn">麦门最强餐品争霸赛</div>
      </div>

      <div className="card-hero">
        <FoodArt code={champion.code} size={150} />
        <div style={{ minWidth: 0 }}>
          <h2 className="card-champ-name">{champion.name}</h2>
          <div className="card-badge">{badge}</div>
          <div style={{ marginTop: 10, color: '#ffc72c', fontSize: 18, fontWeight: 700 }}>
            我的麦门冠军 · {priceLabel(champion)}
          </div>
        </div>
      </div>

      <p className="card-quote">{quote}</p>

      <div className="card-results">
        {route.map((r, i) => (
          <div className="card-result-item" key={i}>
            <div className="card-result-round">{ROUND_LABEL[r.round]}</div>
            <div className="card-result-text">击败 {r.opponent}</div>
          </div>
        ))}
        {route.length < 3 && (
          <div className="card-result-item">
            <div className="card-result-round">战绩</div>
            <div className="card-result-text">7 场全胜登顶</div>
          </div>
        )}
      </div>

      <div className="card-foot">
        <div>
          数据来源：麦当劳官方 MCP · {snapshot.store.name}（{snapshot.store.code}）
        </div>
        <div>
          采集时间：{collectedLabel(snapshot)}
          {snapshot.mode === 'demo-snapshot' ? '（官方数据快照，非实时）' : ''}
        </div>
        <div>
          营养数据仅在官方营养表精确匹配时展示，未匹配一律标注为暂无可靠数据。本作品为独立开发，非麦当劳官方产品。
        </div>
        <div className="repo">{repoUrl}</div>
      </div>
    </div>
  )
}

```

### `src/components/HomeView.tsx`

```ts
import { FoodArt } from './FoodArt'
import { priceLabel } from '../engine/championTitle'
import { collectedLabel, type Snapshot, type SnapshotItem } from '../types'

interface Props {
  snapshot: Snapshot
  items: SnapshotItem[]
  onStart: () => void
}

export function HomeView({ snapshot, items, onStart }: Props) {
  return (
    <div className="home">
      <svg className="hero-art" width="128" height="112" viewBox="0 0 128 112" aria-hidden>
        <defs>
          <linearGradient id="cupg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffd968" />
            <stop offset="100%" stopColor="#e8a33d" />
          </linearGradient>
        </defs>
        <ellipse cx="64" cy="104" rx="42" ry="8" fill="#000" opacity="0.25" />
        <path d="M32 22h64v22c0 16-14 27-32 27S32 60 32 44z" fill="url(#cupg)" />
        <path d="M28 18h72v8H28z" fill="#ffe9a8" />
        <path d="M40 71h48l-4 14H44z" fill="#e8a33d" />
        <rect x="52" y="85" width="24" height="7" rx="3.5" fill="#c98a2e" />
        <rect x="18" y="30" width="12" height="16" rx="6" fill="#e8352e" />
        <rect x="98" y="30" width="12" height="16" rx="6" fill="#e8352e" />
        <path d="M64 4l6 12-6 3-6-3z" fill="#ffc72c" />
      </svg>

      <h1 className="hero-title">麦门最强餐品争霸赛</h1>
      <p className="hero-en">McBracket</p>
      <p className="hero-sub">8 款餐品，7 场对决，只有一个冠军</p>

      <div className="btn-row" style={{ marginTop: 22 }}>
        <button className="btn btn-primary" onClick={onStart} data-testid="start">
          开始我的麦门争霸赛
        </button>
      </div>

      <div className="roster">
        <div className="roster-title">本 期 八 强</div>
        <div className="roster-grid">
          {items.map((it) => (
            <div className="roster-item" key={it.code}>
              <FoodArt code={it.code} size={54} />
              <div className="roster-name">{it.name}</div>
              <div className="roster-price">{priceLabel(it)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="source">
        <div>
          <b>数据来源</b>：麦当劳官方 MCP（{snapshot.toolsUsed.join('、')}）
        </div>
        <div>
          <b>采集门店</b>：{snapshot.store.name}（门店号 {snapshot.store.code}）
        </div>
        <div>
          <b>采集时间</b>：{collectedLabel(snapshot)}
          {snapshot.mode === 'demo-snapshot' ? '（官方数据快照，非实时）' : '（实时查询）'}
        </div>
      </div>
    </div>
  )
}

```

### `src/components/BracketView.tsx`

```ts
import { ROUND_LABEL, type Match, type Round } from '../engine/tournament'

interface Props {
  matches: Match[]
  picks: Array<string | null>
  nameOf: (code: string | null) => string
  className?: string
}

const ORDER: Round[] = ['QF', 'SF', 'F']

export function BracketView({ matches, picks, nameOf, className }: Props) {
  return (
    <div className={className ? `bracket ${className}` : 'bracket'}>
      {ORDER.map((round) => {
        const group = matches.filter((m) => m.round === round)
        return (
          <div className="bracket-round" key={round}>
            <div className="bracket-round-label">{ROUND_LABEL[round]}</div>
            {group.map((m) => {
              const winner = picks[m.index]
              const cell = (code: string | null) => {
                const isWinner = winner !== null && code === winner
                const pending = !code
                return (
                  <div
                    className={`bracket-cell${isWinner ? ' winner' : ''}${pending ? ' pending' : ''}`}
                    key={code ?? 'tbd'}
                  >
                    <span>{pending ? '待定' : nameOf(code)}</span>
                    {isWinner && <span className="tick">✓</span>}
                  </div>
                )
              }
              return (
                <div className="bracket-match" key={m.index}>
                  {cell(m.slotA)}
                  {cell(m.slotB)}
                </div>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}

```

### `src/components/FoodArt.tsx`

```ts
import { ART_PALETTE, artKind } from '../data/art'

interface Props {
  code: string
  size?: number
  className?: string
}

/** Hand-drawn-in-SVG food glyph. Decorative, never a photograph. */
export function FoodArt({ code, size = 120, className }: Props) {
  const kind = artKind(code)
  const p = ART_PALETTE[kind]
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 120 120',
    className,
    'aria-hidden': true as const,
  }

  if (kind === 'wing') {
    return (
      <svg {...common}>
        <ellipse cx="60" cy="104" rx="34" ry="7" fill="#000" opacity="0.18" />
        <path d="M74 30c14 8 20 22 14 34-5 11-18 15-28 11L44 92a7 7 0 1 1-11-8l17-19c-6-10-3-22 7-27 6-3 12-4 17-8z"
          fill={p.patty} />
        <path d="M74 30c14 8 20 22 14 34-5 11-18 15-28 11l3-5c11 3 21-1 25-11 5-11 0-23-12-29z"
          fill={p.bun} opacity="0.85" />
        <circle cx="72" cy="52" r="6" fill={p.accent} opacity="0.5" />
      </svg>
    )
  }

  if (kind === 'cup') {
    return (
      <svg {...common}>
        <ellipse cx="60" cy="106" rx="32" ry="6" fill="#000" opacity="0.18" />
        <path d="M40 36h40l-5 62a6 6 0 0 1-6 5H51a6 6 0 0 1-6-5z" fill={p.patty} />
        <path d="M40 36h40l-1.2 15H41.2z" fill={p.bun} />
        <rect x="52" y="18" width="7" height="26" rx="3" fill={p.accent} transform="rotate(14 55 31)" />
        <rect x="47" y="52" width="26" height="16" rx="4" fill="#fff" opacity="0.85" />
      </svg>
    )
  }

  if (kind === 'apple') {
    return (
      <svg {...common}>
        <ellipse cx="60" cy="100" rx="32" ry="6" fill="#000" opacity="0.18" />
        {[0, 1, 2].map((i) => (
          <g key={i} transform={`translate(${i * 20 - 18} ${i === 1 ? -6 : 0})`}>
            <path d="M46 34c-12 0-20 10-20 22s9 22 20 22 20-10 20-22-8-22-20-22z" fill={p.patty} />
            <path d="M46 34c-12 0-20 10-20 22h6c0-10 6-17 14-17z" fill={p.accent} opacity="0.55" />
          </g>
        ))}
        <path d="M56 22c4-6 12-7 14-7-1 6-5 10-9 11z" fill={p.accent} />
      </svg>
    )
  }

  // Burgers: bun / lettuce / patty / cheese / bun
  const pattyCount = kind === 'double' || kind === 'angus' ? 2 : 1
  return (
    <svg {...common}>
      <ellipse cx="60" cy="104" rx="36" ry="7" fill="#000" opacity="0.18" />
      {/* top bun */}
      <path d="M22 58c0-19 17-32 38-32s38 13 38 32z" fill={p.bun} />
      <g fill={p.accent} opacity="0.6">
        <circle cx="48" cy="40" r="2.6" />
        <circle cx="66" cy="36" r="2.6" />
        <circle cx="80" cy="45" r="2.6" />
      </g>
      {/* lettuce */}
      <path d="M20 60c6-6 12 4 18-1s12 5 18 0 12 5 18 0 12 5 18 0v7H20z" fill={p.accent} />
      {Array.from({ length: pattyCount }).map((_, i) => (
        <g key={i}>
          <rect x="22" y={68 + i * 9} width="76" height="10" rx="5" fill={p.patty} />
          {i === 0 && <rect x="26" y={78} width="68" height="5" rx="2.5" fill="#F2C230" />}
        </g>
      ))}
      {/* bottom bun */}
      <path d="M22 88h76v6a8 8 0 0 1-8 8H30a8 8 0 0 1-8-8z" fill={p.bun} opacity="0.92" />
    </svg>
  )
}

```

### `scripts/fetch_snapshot.py`

```python
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
    # Named `lastRun` on purpose: this describes only the run that just
    # happened. After several merges it is not the coverage of the file as a
    # whole, and reading it as such would be misleading.
    snapshot['lastRun'] = {
        'at': (official or {}).get('formatted') or (official or {}).get('datetime'),
        'requested': len(SEED_CODES),
        'freshThisRun': len(items),
        'carriedFromPrevious': len(carried),
        'refreshedFromPrevious': len(refreshed),
        'missing': sorted(set(SEED_CODES) - {i['code'] for i in merged}),
    }
    if dropped:
        snapshot['lastRun']['droppedThisRun'] = dropped
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

```

### `src/engine/tournament.test.ts`

```ts
import { describe, expect, it } from 'vitest'
import {
  TOTAL_MATCHES,
  buildMatches,
  championCode,
  championRoute,
  currentMatchIndex,
  eliminatedCodes,
  mulberry32,
  resolve,
  roundProgress,
  shuffle,
} from './tournament'
import { formatYuan } from '../types'

const SEEDS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

/** Plays a whole bracket, always picking the first available slot. */
function playthrough(choice: (a: string, b: string) => string) {
  let picks: Array<string | null> = Array(TOTAL_MATCHES).fill(null)
  for (let step = 0; step < TOTAL_MATCHES; step++) {
    const matches = resolve(buildMatches(SEEDS), picks)
    const idx = currentMatchIndex(matches, picks)
    if (idx === null) throw new Error(`no playable match at step ${step}`)
    const m = matches[idx]
    picks[idx] = choice(m.slotA as string, m.slotB as string)
  }
  return picks
}

describe('bracket shape', () => {
  it('needs exactly eight seeds', () => {
    expect(() => buildMatches(['a', 'b'])).toThrow()
    expect(buildMatches(SEEDS)).toHaveLength(7)
  })

  it('starts with four quarter-finals and empty later rounds', () => {
    const m = buildMatches(SEEDS)
    expect(m.filter((x) => x.round === 'QF')).toHaveLength(4)
    expect(m.filter((x) => x.round === 'SF')).toHaveLength(2)
    expect(m.filter((x) => x.round === 'F')).toHaveLength(1)
    expect(m.slice(4).every((x) => x.slotA === null && x.slotB === null)).toBe(true)
  })

  it('fills later rounds only from recorded winners', () => {
    const picks = ['a', 'c', null, null, null, null, null]
    const m = resolve(buildMatches(SEEDS), picks)
    expect(m[4]).toMatchObject({ slotA: 'a', slotB: 'c' })
    expect(m[5].slotA).toBeNull()
    expect(m[6].slotA).toBeNull()
  })
})

describe('a full playthrough', () => {
  it('always advances the clicked contender and crowns it', () => {
    const picks = playthrough((a) => a)
    expect(picks.filter(Boolean)).toHaveLength(7)
    expect(championCode(picks)).toBe('a')
  })

  it('never crowns anyone but the final winner', () => {
    const picks = playthrough((_a, b) => b)
    expect(championCode(picks)).toBe('h')
  })

  it('eliminates exactly the other seven, each once', () => {
    const picks = playthrough((a) => a)
    const out = eliminatedCodes(resolve(buildMatches(SEEDS), picks), picks)
    expect(out).toHaveLength(7)
    expect(new Set(out).size).toBe(7)
    expect(out).not.toContain(championCode(picks))
  })

  it('reports three opponents on the champion route', () => {
    const picks = playthrough((a) => a)
    const route = championRoute(resolve(buildMatches(SEEDS), picks), 'a')
    expect(route).toHaveLength(3)
    expect(route.map((r) => r.round)).toEqual(['QF', 'SF', 'F'])
  })

  it('counts progress from zero to seven', () => {
    let picks: Array<string | null> = Array(TOTAL_MATCHES).fill(null)
    expect(roundProgress(buildMatches(SEEDS), picks).done).toBe(0)
    for (let i = 0; i < TOTAL_MATCHES; i++) {
      const matches = resolve(buildMatches(SEEDS), picks)
      const idx = currentMatchIndex(matches, picks)
      picks[idx as number] = matches[idx as number].slotA as string
      expect(roundProgress(buildMatches(SEEDS), picks).done).toBe(i + 1)
    }
    expect(currentMatchIndex(resolve(buildMatches(SEEDS), picks), picks)).toBeNull()
  })

  it('produces a champion for 200 random playthroughs', () => {
    const rand = mulberry32(20261014)
    for (let n = 0; n < 200; n++) {
      const seeds = shuffle(SEEDS, rand)
      let picks: Array<string | null> = Array(TOTAL_MATCHES).fill(null)
      for (let step = 0; step < TOTAL_MATCHES; step++) {
        const matches = resolve(buildMatches(seeds), picks)
        const idx = currentMatchIndex(matches, picks) as number
        const m = matches[idx]
        picks[idx] = rand() < 0.5 ? (m.slotA as string) : (m.slotB as string)
      }
      const champ = championCode(picks)
      expect(SEEDS).toContain(champ)
      const elim = eliminatedCodes(resolve(buildMatches(seeds), picks), picks)
      expect(new Set(elim).size).toBe(7)
      expect(elim).not.toContain(champ)
    }
  })
})

describe('money', () => {
  it('renders cents as yuan and never guesses', () => {
    expect(formatYuan(2550)).toBe('¥25.5')
    expect(formatYuan(700)).toBe('¥7')
    expect(formatYuan(null)).toBe('暂无可靠数据')
  })
})

describe('shuffle', () => {
  it('keeps every seed and is reproducible', () => {
    const a = shuffle(SEEDS, mulberry32(7))
    const b = shuffle(SEEDS, mulberry32(7))
    expect(a).toEqual(b)
    expect([...a].sort()).toEqual([...SEEDS].sort())
  })
})

```

---

## 6. 审查完请回答

1. **有没有任何一处「说了但没做到」？**（最高优先级）
2. 数据真实性上，最可能被评委抓出来的漏洞是什么？
3. 如果只能改一件事来提高 Star 数，改什么？
