import { FoodArt } from './FoodArt'
import { priceLabel } from '../engine/championTitle'
import type { Snapshot, SnapshotItem } from '../types'

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
          <b>采集时间</b>：{snapshot.collectedAt} {snapshot.collectedAtTimezone}
          {snapshot.mode === 'demo-snapshot' ? '（官方数据快照，非实时）' : '（实时查询）'}
        </div>
      </div>
    </div>
  )
}
