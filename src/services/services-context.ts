import { createContext, useContext } from "react"

import type { AuthApi } from "@/api/auth-api"

// DI for the data layer. The context + hook live here (no component) so the
// provider file can export only a component (Fast Refresh friendly). Tests pass
// fakes via the provider's `value` — the equivalent of overriding a DI provider.
export interface Services {
  authApi: AuthApi
}

export const ServicesContext = createContext<Services | null>(null)

export function useServices(): Services {
  const ctx = useContext(ServicesContext)
  if (!ctx) {
    throw new Error("useServices must be used within a ServicesProvider")
  }
  return ctx
}
