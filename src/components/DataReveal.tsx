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
