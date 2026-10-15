import {
  effectivePriceCents,
  formatYuan,
  priceSourceLabel,
  priceStamp,
  type SnapshotItem,
} from '../types'

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
  if (av === null && bv === null) {
    return (
      <div className="reveal-row">
        <div className="val a lower">暂无可靠数据</div>
        <div className="lbl">{label}</div>
        <div className="val b lower">暂无可靠数据</div>
      </div>
    )
  }
  // One side may still have a value while the other is missing: show the
  // value, an em dash for the missing side, and no higher/lower colouring
  // because a comparison against "unknown" is not a comparison.
  const cell = (v: number | null, other: number | null, side: 'a' | 'b') => {
    if (v === null) return <div className={`val ${side} lower`}>—</div>
    const cls = other === null ? '' : v > other ? 'higher' : v < other ? 'lower' : ''
    return (
      <div className={`val ${side} ${cls}`}>
        {fmt(v)}
        {unit}
      </div>
    )
  }
  return (
    <div className="reveal-row">
      {cell(av, bv, 'a')}
      <div className="lbl">{label}</div>
      {cell(bv, av, 'b')}
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

  // Say which side the price really came from when the two differ, and when
  // each side's evidence was captured — a carried row can be a day older.
  const provenance = a.priceSource !== b.priceSource
    ? ` 价格口径：${a.name}=${priceSourceLabel(a)}，${b.name}=${priceSourceLabel(b)}。`
    : ''
  const stamps = a.collectedAt !== b.collectedAt
    ? ` 采集时间：${a.name} ${priceStamp(a)}，${b.name} ${priceStamp(b)}。`
    : ''
  const carried = a.carried || b.carried
    ? ' 其中标注「沿用」的商品在最近一次采集时未在售，展示的是上次在售时采集的官方数据。'
    : ''

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
        {provenance}
        {stamps}
        {carried}
      </div>
      <div className="next-row">
        <button className="btn btn-primary" onClick={onNext} data-testid="next">
          {isLast ? '查看我的麦门冠军' : '下一场 →'}
        </button>
      </div>
    </div>
  )
}
