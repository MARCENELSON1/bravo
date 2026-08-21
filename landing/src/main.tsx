import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import "@/index.css"
import { App } from "@/App"
import { createContainer } from "@/infrastructure/di/container"
import { ContainerProvider } from "@/presentation/providers/container-provider"

// Composition root en el borde de la app: se construye el contenedor una sola vez
// y se inyecta hacia adentro vía contexto.
const container = createContainer()

const root = document.getElementById("root")
if (!root) throw new Error("No se encontró el elemento #root")

createRoot(root).render(
  <StrictMode>
    <ContainerProvider container={container}>
      <App />
    </ContainerProvider>
  </StrictMode>,
)
