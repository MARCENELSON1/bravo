import { useQuery } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

// Carta pública por token de QR. Sin auth; el token es el scope del tenant.
// `retry: false` → un token inválido no reintenta (muestra el estado enseguida).
export function usePublicMenu(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useQuery({
    queryKey: ["public-menu", token],
    queryFn: () => publicMenuApi.getMenu(token!),
    enabled: !!token,
    retry: false,
  })
}
