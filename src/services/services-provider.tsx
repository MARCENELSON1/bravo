import { useMemo } from "react"
import type { ReactNode } from "react"

import { AuthApi } from "@/api/auth-api"
import { FetchHttpClient } from "@/api/http-client"
import { API_BASE_URL } from "@/lib/env"
import { ServicesContext } from "@/services/services-context"
import type { Services } from "@/services/services-context"

export function ServicesProvider({
  children,
  value,
}: {
  children: ReactNode
  value?: Services
}) {
  const services = useMemo<Services>(
    () => value ?? { authApi: new AuthApi(new FetchHttpClient(API_BASE_URL)) },
    [value]
  )
  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>
}
