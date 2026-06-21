import { useMutation } from "@tanstack/react-query"

import type { OnboardingPayload } from "@/api/types"
import { useServices } from "@/services/services-context"

export function useOnboarding() {
  const { authApi } = useServices()
  return useMutation({
    mutationFn: (payload: OnboardingPayload) => authApi.onboard(payload),
  })
}
