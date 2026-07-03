// Wellnod isotype — the helix/circuit mark, vectorized. Transparent background,
// inherits color via `currentColor` (set it with a text-* class).
const HELIX = [
  { y: 6, a: 22.0, b: 22.0, r: 2.4 },
  { y: 12, a: 28.7, b: 15.3, r: 2.2 },
  { y: 18, a: 29.3, b: 14.7, r: 2.1 },
  { y: 24, a: 23.4, b: 20.6, r: 2.0 },
  { y: 30, a: 16.2, b: 27.8, r: 1.9 },
  { y: 36, a: 14.2, b: 29.8, r: 1.7 },
  { y: 42, a: 19.2, b: 24.8, r: 1.6 },
  { y: 48, a: 26.7, b: 17.3, r: 1.5 },
]

export function WellnodMark({ className }: { className?: string }) {
  const strandA = HELIX.map((p) => `${p.a},${p.y}`).join(" ")
  const strandB = HELIX.map((p) => `${p.b},${p.y}`).join(" ")
  return (
    <svg viewBox="0 0 44 54" fill="none" className={className} aria-hidden>
      <polyline
        points={strandA}
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.85"
      />
      <polyline
        points={strandB}
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.85"
      />
      {HELIX.map((p) => (
        <line
          key={`r${p.y}`}
          x1={p.a}
          y1={p.y}
          x2={p.b}
          y2={p.y}
          stroke="currentColor"
          strokeWidth="0.9"
          opacity="0.35"
        />
      ))}
      {HELIX.map((p) => (
        <g key={`d${p.y}`} fill="currentColor">
          <circle cx={p.a} cy={p.y} r={p.r} />
          <circle cx={p.b} cy={p.y} r={p.r} />
        </g>
      ))}
    </svg>
  )
}
