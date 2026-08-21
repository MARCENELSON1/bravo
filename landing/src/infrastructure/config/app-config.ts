// Configuración de entorno de la landing. Aísla el acceso a import.meta.env en un
// solo lugar (SRP): el resto de la app recibe un objeto tipado.
export interface AppConfig {
  /** URL base de la app Wellnod (donde viven /login y /onboarding). */
  readonly appUrl: string
  readonly loginPath: string
  readonly registerPath: string
}

export function loadConfig(): AppConfig {
  const appUrl = import.meta.env.VITE_APP_URL ?? "http://localhost:5173"
  return {
    appUrl: appUrl.replace(/\/$/, ""),
    loginPath: "/login",
    registerPath: "/onboarding",
  }
}

export function loginUrl(config: AppConfig): string {
  return `${config.appUrl}${config.loginPath}`
}

export function registerUrl(config: AppConfig): string {
  return `${config.appUrl}${config.registerPath}`
}
