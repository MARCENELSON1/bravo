import { StrictMode } from "react"
import { createRoot, hydrateRoot } from "react-dom/client"

import "@/index.css"
import { App } from "@/App"
import { createContainer } from "@/infrastructure/di/container"
import { ContainerProvider } from "@/presentation/providers/container-provider"

// Composition root en el borde de la app: se construye el contenedor una sola vez
// y se inyecta hacia adentro vía contexto.
const container = createContainer()

const root = document.getElementById("root")
if (!root) throw new Error("No se encontró el elemento #root")

const tree = (
  <StrictMode>
    <ContainerProvider container={container}>
      <App />
    </ContainerProvider>
  </StrictMode>
)

// El build prerenderiza el HTML (ver scripts/prerender.mjs). Si el root ya viene
// pintado, React se engancha a ese markup en vez de tirarlo y volver a dibujar;
// si está vacío (por ejemplo en `vite dev`), monta normal.
if (root.hasChildNodes()) {
  hydrateRoot(root, tree)
} else {
  createRoot(root).render(tree)
}
