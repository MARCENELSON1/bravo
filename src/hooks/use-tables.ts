import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useServices } from "@/services/services-context"

export function useTables() {
  const { tablesApi } = useServices()
  return useQuery({ queryKey: ["tables"], queryFn: () => tablesApi.list() })
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
