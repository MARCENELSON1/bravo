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
  const services: Services = {
    advisorApi: {} as unknown as Services["advisorApi"],
    analyticsApi: {} as unknown as Services["analyticsApi"],
    authApi: makeFakeAuthApi(authApi),
    copilotApi: {} as unknown as Services["copilotApi"],
    integrationsApi: {} as unknown as Services["integrationsApi"],
    inventoryApi: {} as unknown as Services["inventoryApi"],
    invoicesApi: {} as unknown as Services["invoicesApi"],
    ordersApi: {} as unknown as Services["ordersApi"],
    paymentsApi: {} as unknown as Services["paymentsApi"],
    productsApi: {} as unknown as Services["productsApi"],
    realtimeApi: {} as unknown as Services["realtimeApi"],
    reportsApi: {} as unknown as Services["reportsApi"],
    reservationsApi: {} as unknown as Services["reservationsApi"],
    tablesApi: {} as unknown as Services["tablesApi"],
    timeClockApi: {} as unknown as Services["timeClockApi"],
  }
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
