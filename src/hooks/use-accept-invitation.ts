import { useMutation } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

interface AcceptInvitationVars {
  token: string
  password: string
}

export function useAcceptInvitation() {
  const { authApi } = useServices()
  return useMutation({
    mutationFn: (vars: AcceptInvitationVars) =>
      authApi.acceptInvitation(vars.token, vars.password),
  })
}
