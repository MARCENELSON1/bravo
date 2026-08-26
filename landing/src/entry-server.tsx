/**
 * Punto de entrada de SSG. NO corre en el navegador: lo usa `scripts/prerender.mjs`
 * en tiempo de build para generar el HTML estático que sirve Railway.
 *
 * Existe porque la landing es un SPA: sin esto el servidor entrega un <div> vacío
 * y los crawlers que no ejecutan JavaScript — que son todos los de los motores de
 * respuesta (GPTBot, PerplexityBot, ClaudeBot) — ven una página en blanco.
 */
import { StrictMode } from "react"
import { renderToString } from "react-dom/server"

import { App } from "@/App"
import type { Region } from "@/domain/value-objects/region"
import { createContainer } from "@/infrastructure/di/container"
import { ContainerProvider } from "@/presentation/providers/container-provider"
import { buildStructuredData } from "@/infrastructure/seo/structured-data"

export function render(region: Region = "AR"): string {
  const container = createContainer(region)
  return renderToString(
    <StrictMode>
      <ContainerProvider container={container}>
        <App />
      </ContainerProvider>
    </StrictMode>,
  )
}

/** JSON-LD derivado de los MISMOS repositorios que pintan la pantalla. */
export async function structuredData(region: Region = "AR"): Promise<string> {
  const container = createContainer(region)
  return buildStructuredData(container)
}
