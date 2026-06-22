import { useMutation } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useAskCopilot() {
  const { copilotApi } = useServices()
  return useMutation({
    mutationFn: (question: string) => copilotApi.ask(question),
  })
}
