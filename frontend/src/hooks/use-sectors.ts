import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { SectorInput } from "@/api/sectors-api"
import { useServices } from "@/services/services-context"

export function useSectors() {
  const { sectorsApi } = useServices()
  return useQuery({ queryKey: ["sectors"], queryFn: () => sectorsApi.list() })
}

function useInvalidateSectors() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: ["sectors"] })
    void queryClient.invalidateQueries({ queryKey: ["floor"] })
  }
}

export function useCreateSector() {
  const { sectorsApi } = useServices()
  const invalidate = useInvalidateSectors()
  return useMutation({
    mutationFn: (input: SectorInput) => sectorsApi.create(input),
    onSuccess: invalidate,
  })
}

export function useUpdateSector() {
  const { sectorsApi } = useServices()
  const invalidate = useInvalidateSectors()
  return useMutation({
    mutationFn: (vars: { id: string; input: SectorInput }) =>
      sectorsApi.update(vars.id, vars.input),
    onSuccess: invalidate,
  })
}

export function useDeleteSector() {
  const { sectorsApi } = useServices()
  const invalidate = useInvalidateSectors()
  return useMutation({
    mutationFn: (id: string) => sectorsApi.remove(id),
    onSuccess: invalidate,
  })
}
