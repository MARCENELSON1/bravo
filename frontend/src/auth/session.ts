import type { Role } from "@/api/types"

// What the SPA knows about the signed-in user. Hydrated from GET /ping, which
// carries the access-token claims (no email — see MeResponse).
export interface Session {
  userId: string
  tenantId: string
  role: Role
}
