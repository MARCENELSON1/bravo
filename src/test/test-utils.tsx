import type { ReactNode } from "react"
import { render } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { vi } from "vitest"

import { ApiError } from "@/api/api-error"
import type { AuthApi } from "@/api/auth-api"
import { AuthProvider } from "@/auth/auth-provider"
import { ServicesProvider } from "@/services/services-provider"
import type { Services } from "@/services/services-context"

// A fake AuthApi (the equivalent of overriding a DI container provider in the
// backend). `refresh` rejects by default → the AuthProvider boots to anonymous.
export function makeFakeAuthApi(overrides: Partial<AuthApi> = {}): AuthApi {
  const fake = {
    refresh: vi.fn().mockRejectedValue(new ApiError("invalid_token", "sin sesión", 401)),
    me: vi.fn(),
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    onboard: vi.fn(),
    verifyEmail: vi.fn(),
    acceptInvitation: vi.fn(),
    inviteUser: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
    changePassword: vi.fn(),
    ...overrides,
  }
  return fake as unknown as AuthApi
}

export function renderWithProviders(
  ui: ReactNode,
  { authApi, route = "/" }: { authApi?: Partial<AuthApi>; route?: string } = {}
) {
  const services: Services = { authApi: makeFakeAuthApi(authApi) }
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ServicesProvider value={services}>
        <AuthProvider>
          <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
        </AuthProvider>
      </ServicesProvider>
    </QueryClientProvider>
  )
}
