import { useMutation } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useVerifyEmail() {
  const { authApi } = useServices()
  return useMutation({
    mutationFn: (token: string) => authApi.verifyEmail(token),
  })
}
