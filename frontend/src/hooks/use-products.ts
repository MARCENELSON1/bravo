import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { Station } from "@/api/types-operations"
import { useServices } from "@/services/services-context"

export function useProducts() {
  const { productsApi } = useServices()
  return useQuery({ queryKey: ["products"], queryFn: () => productsApi.list() })
}

interface CreateProductVars {
  name: string
  priceAmount: number
  category: string | null
  station: Station
}

export function useCreateProduct() {
  const { productsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: CreateProductVars) =>
      productsApi.create(vars.name, vars.priceAmount, vars.category, vars.station),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["products"] })
    },
  })
}
