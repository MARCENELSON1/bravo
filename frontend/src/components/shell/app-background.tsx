import { cn } from "@/lib/utils"

// Fondo escénico de la app, en dos escenas.
//
// El gradiente de base es el mismo en las dos, y es el del login: un neutro casi
// negro. La consola le suma encima la textura, con los MISMOS valores que el mockup
// del hero de la landing —valor por valor— así lo que se promete en la web es lo que
// se ve al entrar.
//
// La textura va desaturada y en `soft-light`: la foto es verde, y a color le
// devolvería a la base el tinte que justamente no tiene que tener; en `soft-light`
// modula el valor en vez de taparlo, que con opacidad plana lo aplastaba.
//
// Lo que separa a las dos escenas es el cierre. "identity" —el login y sus pantallas
// hermanas— va sin textura y con viñeta: ahí el fondo se ve directo, sin los paneles
// de vidrio que en la consola filtran y suavizan todo lo que tienen detrás, así que
// el mismo tratamiento pesa mucho más. Y en la consola la viñeta oscurecía los
// bordes, que es justo donde se apoyan los paneles.
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
      {/* Base por tema, la misma en las dos escenas. */}
      <div className="absolute inset-0 bg-[radial-gradient(125%_125%_at_18%_12%,#f6f6f6_0%,#e9e9e9_50%,#d7d7d7_100%)] dark:bg-[radial-gradient(125%_125%_at_18%_12%,#1d1d1d_0%,#131313_52%,#0a0a0a_100%)]" />

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
          className="bg-texture absolute inset-0 bg-cover bg-center bg-no-repeat opacity-50 grayscale mix-blend-soft-light"
          style={{ backgroundImage: "url('/app-bg-texture.webp')" }}
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
