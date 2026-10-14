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
