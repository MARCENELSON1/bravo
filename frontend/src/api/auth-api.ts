import type { HttpClient } from "@/api/http-client"
import { clearAccessToken, setAccessToken } from "@/api/token-store"
import type {
  AccessTokenResponse,
  MeResponse,
  MessageResponse,
  OnboardingPayload,
  OnboardingResponse,
  Role,
} from "@/api/types"

// Identity client. Thin wrappers over the auth endpoints; injected through the
// ServicesProvider so screens/hooks never touch fetch or build URLs themselves.
export class AuthApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  // OAuth2 password flow: the tenant slug travels in `client_id`.
  async login(slug: string, email: string, password: string): Promise<void> {
    const form = new URLSearchParams({
      username: email,
      password,
      client_id: slug,
    })
    const res = await this.http.request<AccessTokenResponse>("POST", "/auth/login", { form })
    setAccessToken(res.access_token)
  }

  // Silent refresh against the HttpOnly cookie (used on app boot).
  async refresh(): Promise<void> {
    const res = await this.http.request<AccessTokenResponse>("POST", "/auth/refresh", {})
    setAccessToken(res.access_token)
  }

  async logout(): Promise<void> {
    try {
      await this.http.request<MessageResponse>("POST", "/auth/logout", {})
    } finally {
      clearAccessToken()
    }
  }

  // "Whoami" with human-facing names (user + tenant) — feeds the app shell.
  async me(): Promise<MeResponse> {
    return this.http.request<MeResponse>("GET", "/me", { auth: true })
  }

  async onboard(payload: OnboardingPayload): Promise<OnboardingResponse> {
    return this.http.request<OnboardingResponse>("POST", "/tenants/onboarding", { body: payload })
  }

  async verifyEmail(token: string): Promise<MessageResponse> {
    return this.http.request<MessageResponse>("POST", "/auth/verify-email", { body: { token } })
  }

  async acceptInvitation(token: string, password: string): Promise<MessageResponse> {
    return this.http.request<MessageResponse>("POST", "/users/accept-invitation", {
      body: { token, password },
    })
  }

  async inviteUser(email: string, role: Role): Promise<MessageResponse> {
    return this.http.request<MessageResponse>("POST", "/users/invite", {
      body: { email, role },
      auth: true,
    })
  }

  // --- Full auth surface (clients ready; screens deferred for this slice) ---

  async forgotPassword(tenantSlug: string, email: string): Promise<MessageResponse> {
    return this.http.request<MessageResponse>("POST", "/auth/forgot-password", {
      body: { tenant_slug: tenantSlug, email },
    })
  }

  async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
    return this.http.request<MessageResponse>("POST", "/auth/reset-password", {
      body: { token, new_password: newPassword },
    })
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<MessageResponse> {
    return this.http.request<MessageResponse>("POST", "/auth/change-password", {
      body: { current_password: currentPassword, new_password: newPassword },
      auth: true,
    })
  }
}
