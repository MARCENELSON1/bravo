import { cn } from "@/lib/utils"

// Fondo escénico de la app, en dos escenas.
//
// "console" es la consola: gradiente verde, textura y grano con los MISMOS valores
// que el mockup del hero de la landing —valor por valor— así lo que se promete en la
// web es lo que se ve al entrar. La textura va en `soft-light`, que modula el verde
// en vez de taparlo; con opacidad plana lo aplastaba y lo dejaba grisado. Sin viñeta:
// oscurecía los bordes, que es justo donde se apoyan los paneles, y hacía ver la
// pantalla más cerrada que la maqueta.
//
// "identity" es el login y sus pantallas hermanas: el fondo neutro de siempre, con
// viñeta y sin textura. Ahí el fondo se ve directo, sin los paneles de vidrio que en
// la consola filtran y suavizan todo lo que tienen detrás, así que el mismo
// tratamiento pesa mucho más.
//
// Las manchas de luz son de las dos: es lo que le da vida al fondo sin cambiarle el
// color de base.
export function AppBackground({
  scene = "console",
}: {
  scene?: "console" | "identity"
} = {}) {
  const identity = scene === "identity"

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {/* Base por tema. */}
      <div
        className={cn(
          "absolute inset-0",
          identity
            ? "bg-[radial-gradient(125%_125%_at_18%_12%,#f6f6f6_0%,#e9e9e9_50%,#d7d7d7_100%)] dark:bg-[radial-gradient(125%_125%_at_18%_12%,#1d1d1d_0%,#131313_52%,#0a0a0a_100%)]"
            : "bg-[radial-gradient(125%_125%_at_18%_12%,#d7e6df_0%,#aec7bb_50%,#85a394_100%)] dark:bg-[radial-gradient(125%_125%_at_18%_12%,#2a4b43_0%,#16241f_52%,#0a120e_100%)]"
        )}
      />

      {/* Grano fino. Va DEBAJO de las manchas: su mezcla es cara y arriba se
          recalcularía en cada cuadro de la animación. */}
      <div
        className={cn(
          "bg-grain absolute inset-0 mix-blend-overlay",
          identity ? "opacity-[0.12]" : "opacity-[0.18]"
        )}
      />

      {/* Textura, solo en la consola. */}
      {identity ? null : (
        <div
          className="bg-texture absolute inset-0 bg-cover bg-center bg-no-repeat opacity-50 mix-blend-soft-light"
          style={{ backgroundImage: "url('/app-bg-dark.png')" }}
        />
      )}

      {/* Manchas de luz. Derivan solas, muy lento; sin parallax porque el shell no
          scrollea la ventana. */}
      <div className="aurora aurora-a" />
      <div className="aurora aurora-b" />
      <div className="aurora aurora-c" />

      {/* Viñeta: cierra los bordes y concentra la atención en el centro. Solo en las
          pantallas de identidad, donde no hay panel que ocupe todo. */}
      {identity ? <div className="vignette" /> : null}
    </div>
  )
}
