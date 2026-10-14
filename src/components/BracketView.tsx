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
