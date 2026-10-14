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
