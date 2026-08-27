import { useMutation } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

interface ResetPasswordVars {
  token: string
  password: string
}

// Setea la nueva contraseña con el token del correo (endpoint ya existente).
export function useResetPassword() {
  const { authApi } = useServices()
  return useMutation({
    mutationFn: (vars: ResetPasswordVars) => authApi.resetPassword(vars.token, vars.password),
  })
}
