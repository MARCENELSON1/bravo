import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { CustomerInput } from "@/api/customers-api"
import { useServices } from "@/services/services-context"

export function useCustomers(search?: string) {
  const { customersApi } = useServices()
  return useQuery({
    queryKey: ["customers", search ?? ""],
    queryFn: () => customersApi.list(search),
  })
}

function useInvalidateCustomers() {
  const queryClient = useQueryClient()
  return () => void queryClient.invalidateQueries({ queryKey: ["customers"] })
}

export function useCreateCustomer() {
  const { customersApi } = useServices()
  const invalidate = useInvalidateCustomers()
  return useMutation({
    mutationFn: (input: CustomerInput) => customersApi.create(input),
    onSuccess: invalidate,
  })
}

export function useUpdateCustomer() {
  const { customersApi } = useServices()
  const invalidate = useInvalidateCustomers()
  return useMutation({
    mutationFn: (vars: { id: string; input: CustomerInput }) =>
      customersApi.update(vars.id, vars.input),
    onSuccess: invalidate,
  })
}

export function useDeleteCustomer() {
  const { customersApi } = useServices()
  const invalidate = useInvalidateCustomers()
  return useMutation({
    mutationFn: (id: string) => customersApi.remove(id),
    onSuccess: invalidate,
  })
}
