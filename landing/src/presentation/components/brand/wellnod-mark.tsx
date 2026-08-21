// Isotipo Wellnod — helix trazado real de la marca, con puntos sólidos (sin huecos).
// Fondo transparente, hereda el color vía `currentColor`.
export function WellnodMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="96 232 68 162"
      className={className}
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
    >
      <g
        transform="translate(0.000000,600.000000) scale(0.100000,-0.100000)"
        fill="currentColor"
        stroke="none"
      >
        <path d="M1080 3560 c-24 -24 -26 -53 -4 -74 32 -33 94 -10 94 35 0 23 -34 59 -55 59 -8 0 -24 -9 -35 -20z" />
        <path d="M1192 3438 c-27 -27 -4 -78 35 -78 40 0 57 45 27 74 -18 19 -45 21 -62 4z" />
        <path d="M1326 3342 c-2 -4 -7 -23 -11 -42 -8 -42 -65 -90 -106 -90 -48 0 -62 -57 -19 -80 21 -11 60 13 60 38 1 35 81 102 122 102 22 0 35 45 18 65 -13 16 -55 21 -64 7z" />
        <path d="M1470 3250 c-6 -4 -19 -19 -28 -34 -12 -20 -54 -44 -147 -87 -116 -53 -135 -59 -176 -53 -42 5 -46 3 -57 -21 -10 -21 -10 -31 -1 -41 17 -21 57 -17 71 7 12 20 70 50 239 125 58 25 84 32 111 28 31 -5 37 -3 43 15 13 43 -21 82 -55 61z" />
        <path d="M1523 3088 c-9 -20 -50 -38 -221 -100 -191 -69 -214 -76 -242 -65 -26 10 -33 9 -51 -10 -26 -26 -18 -60 17 -69 26 -7 54 10 54 32 0 8 -1 16 -3 23 7 -7 26 -4 64 11 30 12 92 35 139 51 47 17 114 42 149 56 43 16 76 23 97 20 41 -7 67 11 62 44 -4 34 -50 39 -65 7z" />
        <path d="M1513 2931 c-3 -11 -10 -22 -16 -24 -7 -3 -95 -37 -196 -76 -167 -65 -187 -71 -213 -60 -41 17 -78 -4 -78 -42 0 -30 23 -49 59 -49 19 0 46 32 35 42 -6 7 71 43 166 79 41 15 113 43 160 62 47 19 90 32 95 29 30 -19 51 3 40 39 -8 25 -45 24 -52 0z" />
        <path d="M1414 2793 c-3 -10 -48 -45 -101 -77 -76 -47 -103 -59 -134 -58 -58 3 -88 -37 -53 -72 29 -29 66 -18 83 25 10 28 179 140 216 144 11 1 24 3 28 4 5 0 7 11 5 23 -4 29 -38 37 -44 11z" />
        <path d="M1248 2545 c-14 -31 3 -55 39 -55 32 0 47 38 25 63 -22 24 -51 21 -64 -8z" />
        <path d="M1371 2461 c-16 -30 -3 -53 28 -49 22 2 26 8 26 33 0 23 -5 31 -22 33 -14 2 -26 -4 -32 -17z" />
        <path d="M1434 2335 c-4 -8 -3 -22 0 -31 8 -21 50 -14 54 10 6 31 -43 50 -54 21z" />
        <path d="M1404 2196 c-9 -24 4 -48 23 -44 24 4 24 52 0 56 -9 2 -20 -4 -23 -12z" />
        <path d="M1035 2889 c-4 -6 -5 -12 -2 -15 2 -3 7 2 10 11 7 17 1 20 -8 4z" />
      </g>
    </svg>
  )
}

// Isotipo + wordmark "Wellnod", como en la app.
export function WellnodLogo({ className }: { className?: string }) {
  return (
    <span className={className}>
      <span className="inline-flex items-center gap-2 text-foreground">
        <WellnodMark className="h-7 w-auto" />
        <span className="font-brand text-xl leading-none tracking-tight">
          <span className="font-bold">Well</span>
          <span className="-ml-[3px] font-light text-foreground/55">nod</span>
        </span>
      </span>
    </span>
  )
}
