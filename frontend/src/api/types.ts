// DTOs mirror the backend contract exactly (English field names).

export type Role = "OWNER" | "MANAGER" | "WAITER" | "KITCHEN" | "BAR" | "CASHIER"

// Roles an OWNER/MANAGER may grant via invitation (OWNER is never invitable).
export const INVITABLE_ROLES: Role[] = ["MANAGER", "WAITER", "KITCHEN", "BAR", "CASHIER"]

export interface AccessTokenResponse {
  access_token: string
  token_type: string
}

export interface MessageResponse {
  message: string
}

// GET /api/v1/ping — the "whoami". Note it does NOT include the email.
export interface MeResponse {
  tenant_id: string
  user_id: string
  role: Role
}

export interface OnboardingPayload {
  tenant_name: string
  tenant_slug: string
  owner_email: string
  owner_password: string
}

export interface OnboardingResponse {
  tenant_id: string
  user_id: string
  message: string
}
