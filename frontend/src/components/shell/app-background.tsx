// Fondo escénico de la app: gradiente neutro, tres manchas de luz sin tinte,
// viñeta y grano. Es el mismo tratamiento que la landing —los tokens de color ya
// eran idénticos entre las dos, así que ahora también coincide el fondo.
//
// El verde quedó reservado para la marca y los acentos: cuando el fondo también
// era verde, el acento dejaba de destacarse contra él.
//
// Reutilizable entre el shell y las pantallas full-screen (ej. Configuración).
export function AppBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Base: gradiente neutro por tema. */}
      <div className="absolute inset-0 bg-[radial-gradient(125%_125%_at_18%_12%,#f6f6f6_0%,#e9e9e9_50%,#d7d7d7_100%)] dark:bg-[radial-gradient(125%_125%_at_18%_12%,#1d1d1d_0%,#131313_52%,#0a0a0a_100%)]" />
      {/* Grano fino. Va DEBAJO de las manchas: su mezcla es cara y arriba se
          recalculaba en cada cuadro de la animación. */}
      <div className="bg-grain absolute inset-0 opacity-[0.12] mix-blend-overlay" />

      {/* Manchas de luz. Derivan solas, muy lento; sin parallax porque el shell no
          scrollea la ventana. */}
      <div className="aurora aurora-a" />
      <div className="aurora aurora-b" />
      <div className="aurora aurora-c" />

      {/* Viñeta: cierra los bordes y concentra la atención en el centro. */}
      <div className="vignette" />

      {/* Grano fino. Va último: unifica todas las capas. */}
    </div>
  )
}
