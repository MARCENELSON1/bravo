import { useCallback, useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { setUnauthorizedHandler } from "@/api/token-store"
import { AuthContext } from "@/auth/auth-context"
import type { AuthContextValue, AuthStatus } from "@/auth/auth-context"
import type { Session } from "@/auth/session"
import { useServices } from "@/services/services-context"

export function AuthProvider({ children }: { children: ReactNode }) {
  const { authApi } = useServices()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<AuthStatus>("booting")
  const [session, setSession] = useState<Session | null>(null)

  // Boot: restore the session via a silent refresh against the HttpOnly cookie.
  // The JS holds no token across reloads, yet the session survives.
  useEffect(() => {
    let active = true
    setUnauthorizedHandler(() => {
      if (!active) return
      setSession(null)
      setStatus("anonymous")
    })

    void (async () => {
      try {
        await authApi.refresh()
        const me = await authApi.me()
        if (!active) return
        setSession({ userId: me.user_id, tenantId: me.tenant_id, role: me.role })
        setStatus("authenticated")
      } catch {
        if (!active) return
        setSession(null)
        setStatus("anonymous")
      }
    })()

    return () => {
      active = false
      setUnauthorizedHandler(null)
    }
  }, [authApi])

  const login = useCallback(
    async (slug: string, email: string, password: string) => {
      await authApi.login(slug, email, password)
      const me = await authApi.me()
      setSession({ userId: me.user_id, tenantId: me.tenant_id, role: me.role })
      setStatus("authenticated")
    },
    [authApi]
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      queryClient.clear()
      setSession(null)
      setStatus("anonymous")
    }
  }, [authApi, queryClient])

  const value = useMemo<AuthContextValue>(
    () => ({ status, session, login, logout }),
    [status, session, login, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
