import { useMutation } from "@tanstack/react-query"

import { useAuth } from "@/auth/auth-context"

interface LoginVars {
  slug: string
  email: string
  password: string
}

// Wraps the AuthProvider login (which sets access token + session) so screens
// get isPending/error ergonomics. Refresh-on-401 lives below, in the http client.
export function useLogin() {
  const { login } = useAuth()
  return useMutation({
    mutationFn: (vars: LoginVars) => login(vars.slug, vars.email, vars.password),
  })
}
