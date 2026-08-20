// Fondo de la app: gradiente verde suave (base) + textura semi-transparente +
// grano. Reutilizable entre el shell y las pantallas full-screen (ej. Config).
export function AppBackground() {
  return (
    <>
      {/* Base: gradiente verde suave (borroso) por tema */}
      <div
        aria-hidden
        className="fixed inset-0 -z-20 bg-[radial-gradient(125%_125%_at_18%_12%,#d7e6df_0%,#aec7bb_50%,#85a394_100%)] dark:bg-[radial-gradient(125%_125%_at_18%_12%,#2a4b43_0%,#16241f_52%,#0a120e_100%)]"
      />
      {/* Textura (imagen) semi-transparente encima del gradiente */}
      <div
        aria-hidden
        className="fixed inset-0 -z-10 bg-cover bg-center bg-no-repeat opacity-50 mix-blend-soft-light dark:hidden"
        style={{ backgroundImage: "url('/app-bg-light.png')" }}
      />
      <div
        aria-hidden
        className="fixed inset-0 -z-10 hidden bg-cover bg-center bg-no-repeat opacity-50 mix-blend-soft-light dark:block"
        style={{ backgroundImage: "url('/app-bg-dark.png')" }}
      />
      {/* Grano/ruido sutil sobre el fondo */}
      <div
        aria-hidden
        className="bg-grain pointer-events-none fixed inset-0 -z-10 opacity-[0.18] mix-blend-overlay"
      />
    </>
  )
}
