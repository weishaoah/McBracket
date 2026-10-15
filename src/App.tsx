import { useCallback, useMemo, useRef, useState } from 'react'
import snapshotJson from './data/snapshot.json'
import { collectedLabel, type Snapshot, type SnapshotItem } from './types'
import {
  buildMatches,
  championCode,
  championRoute,
  currentMatchIndex,
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
/**
 * Defensive de-duplication by code: a corrupted snapshot must never put the
 * same food into two bracket slots, and the bracket needs exactly eight
 * distinct seeds. Anything else renders a data-error panel instead of a
 * half-broken tournament.
 */
const ITEMS: SnapshotItem[] = (() => {
  const seen = new Set<string>()
  return snapshot.items.filter((i) => {
    if (!i || typeof i.code !== 'string' || seen.has(i.code)) return false
    seen.add(i.code)
    return true
  })
})()
const BY_CODE = new Map(ITEMS.map((i) => [i.code, i]))
const ROSTER_OK = ITEMS.length === 8
const REPO_URL = 'https://github.com/weishaoah/McBracket'

type Stage = 'home' | 'playing' | 'champion'

export default function App() {
  const [stage, setStage] = useState<Stage>('home')
  const [order, setOrder] = useState<string[]>(() => ITEMS.map((i) => i.code))
  const [picks, setPicks] = useState<Array<string | null>>(() => Array(7).fill(null))
  /** Which match is on screen; the reveal keeps it visible until 「下一场」. */
  const [rawView, setRawView] = useState(0)
  const [busy, setBusy] = useState<string | null>(null)
  const cardRef = useRef<HTMLDivElement>(null)

  const matches = useMemo(
    () => (ROSTER_OK ? resolve(buildMatches(order), picks) : []),
    [order, picks],
  )
  /**
   * The match on screen must be one whose contenders are known. If the
   * stored index ever points at an empty slot, fall back to the first
   * playable match — so a click can never be written into the wrong
   * bracket slot (a wrong advancement).
   */
  const viewIndex = useMemo(() => {
    const m = matches[rawView]
    if (m && m.slotA && m.slotB) return rawView
    return currentMatchIndex(matches, picks) ?? rawView
  }, [matches, picks, rawView])
  const { done } = roundProgress(matches, picks)
  const champion = championCode(picks)

  const start = useCallback(() => {
    setOrder(shuffle(ITEMS.map((i) => i.code)))
    setPicks(Array(7).fill(null))
    setRawView(0)
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
    else setRawView((v) => Math.min(v + 1, 6))
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

  if (!ROSTER_OK) {
    return (
      <div className="app">
        <div className="topbar">
          <div className="brand">
            <span className="brand-mark">McBracket</span>
            <span className="brand-sub">麦门最强餐品争霸赛</span>
          </div>
        </div>
        <div className="home">
          <h1 className="hero-title">数据快照不完整</h1>
          <p className="hero-sub">
            本期八强需要 8 款不同餐品，当前快照只有 {ITEMS.length} 款
            （门店 {snapshot.store.name}，采集于 {collectedLabel(snapshot)}）。
            请重新运行 scripts/fetch_snapshot.py 采集官方数据后再试。
          </p>
        </div>
      </div>
    )
  }

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

      {stage === 'playing' && matches[viewIndex]?.slotA && matches[viewIndex]?.slotB && (
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
