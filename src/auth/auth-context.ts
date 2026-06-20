import { createContext, useContext } from "react"

import type { Session } from "@/auth/session"

export type AuthStatus = "booting" | "authenticated" | "anonymous"

export interface AuthContextValue {
  status: AuthStatus
  session: Session | null
  login: (slug: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return ctx
}
