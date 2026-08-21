import { loginUrl, registerUrl } from "@/infrastructure/config/app-config"
import { useContainer } from "@/presentation/providers/container-provider"

// Resuelve las URLs de login/registro de la app a partir de la config del contenedor.
export function useAuthLinks() {
  const { config } = useContainer()
  return {
    login: loginUrl(config),
    register: registerUrl(config),
  }
}
