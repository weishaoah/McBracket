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
