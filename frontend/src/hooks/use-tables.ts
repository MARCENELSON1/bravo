import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useTables() {
  const { tablesApi } = useServices()
  return useQuery({ queryKey: ["tables"], queryFn: () => tablesApi.list() })
}

// QR de una mesa (token determinístico → no vence, se cachea indefinidamente).
export function useTableQr(tableId: string) {
  const { tablesApi } = useServices()
  return useQuery({
    queryKey: ["table-qr", tableId],
    queryFn: () => tablesApi.qr(tableId),
    staleTime: Infinity,
  })
}

interface CreateTableVars {
  number: number
  name: string | null
}

export function useCreateTable() {
  const { tablesApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: CreateTableVars) => tablesApi.create(vars.number, vars.name),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["tables"] })
    },
  })
}

export function useUpdateTable() {
  const { tablesApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: {
      tableId: string
      patch: { sector_id?: string | null; capacity?: number | null }
    }) => tablesApi.update(vars.tableId, vars.patch),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["tables"] })
      void queryClient.invalidateQueries({ queryKey: ["floor"] })
    },
  })
}
