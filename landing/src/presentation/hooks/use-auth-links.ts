import { loginUrl, registerUrl } from "@/infrastructure/config/app-config"
import { useContainer } from "@/presentation/providers/container-provider"

// Resuelve las URLs de login/registro de la app a partir de la config del contenedor.
// El REGISTRO lleva el país (ISO-2) de la región → el onboarding de la app crea el
// tenant con la moneda/impuestos/locale correctos (INTL → US/USD, AR → AR/ARS).
// Sin esto el backend caía siempre a AR/ARS aunque el visitante viniera de /en/.
export function useAuthLinks() {
  const { config, region } = useContainer()
  const country = region === "INTL" ? "US" : "AR"
  return {
    login: loginUrl(config),
    register: `${registerUrl(config)}?country=${country}`,
  }
}
