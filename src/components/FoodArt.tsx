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
