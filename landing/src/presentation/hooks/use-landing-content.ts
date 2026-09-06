import { useMemo } from "react"

import { useContainer } from "@/presentation/providers/container-provider"

// Puente entre el caso de uso GetLandingContent y React. Devuelve el contenido en
// el primer render —sin estado ni efecto— para que también salga en el HTML del
// prerender: si esto se llenara en un useEffect, el servidor renderizaría las
// secciones vacías y los buscadores no verían ni un área ni un paso.
export function useLandingContent() {
  const { getLandingContent } = useContainer()
  return useMemo(() => getLandingContent.execute(), [getLandingContent])
}
