import { useMutation } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

interface ForgotPasswordVars {
  slug: string
  email: string
}

// Pide el correo de recuperación (endpoint ya existente en authApi).
export function useForgotPassword() {
  const { authApi } = useServices()
  return useMutation({
    mutationFn: (vars: ForgotPasswordVars) => authApi.forgotPassword(vars.slug, vars.email),
  })
}
