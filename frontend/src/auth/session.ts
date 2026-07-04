import type { Role } from "@/api/types"

// What the SPA knows about the signed-in user. Hydrated from GET /me, which
// reads the human-facing names (user + tenant) behind the access-token claims.
export interface Session {
  userId: string
  tenantId: string
  role: Role
  email: string
  name: string | null
  tenantName: string
}
