import type { ReactNode } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { AuthProvider } from "@/auth/auth-provider"
import { Toaster } from "@/components/ui/sonner"
import { ServicesProvider } from "@/services/services-provider"
import type { Services } from "@/services/services-context"

// Provider tree reused by the whole app (and by tests via `services`):
// data cache (Query) → injectable clients (Services) → session (Auth).
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

export function Providers({
  children,
  services,
}: {
  children: ReactNode
  services?: Services
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <ServicesProvider value={services}>
        <AuthProvider>
          {children}
          <Toaster position="top-center" />
        </AuthProvider>
      </ServicesProvider>
    </QueryClientProvider>
  )
}
