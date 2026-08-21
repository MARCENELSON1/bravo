import { createContext, useContext, type ReactNode } from "react"

import type { Container } from "@/infrastructure/di/container"

// Expone el contenedor de DI a la UI vía contexto. La presentación consume casos de
// uso a través de este provider; nunca construye adapters por su cuenta.
const ContainerContext = createContext<Container | null>(null)

export function ContainerProvider({
  container,
  children,
}: {
  container: Container
  children: ReactNode
}) {
  return <ContainerContext.Provider value={container}>{children}</ContainerContext.Provider>
}

export function useContainer(): Container {
  const container = useContext(ContainerContext)
  if (!container) {
    throw new Error("useContainer debe usarse dentro de <ContainerProvider>")
  }
  return container
}
