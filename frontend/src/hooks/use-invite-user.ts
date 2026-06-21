import { useMutation } from "@tanstack/react-query"

import type { Role } from "@/api/types"
import { useServices } from "@/services/services-context"

interface InviteUserVars {
  email: string
  role: Role
}

export function useInviteUser() {
  const { authApi } = useServices()
  return useMutation({
    mutationFn: (vars: InviteUserVars) => authApi.inviteUser(vars.email, vars.role),
  })
}
