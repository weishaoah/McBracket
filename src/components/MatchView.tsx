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
