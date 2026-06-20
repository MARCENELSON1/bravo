import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { OrderAction } from "@/api/orders-api"
import { useServices } from "@/services/services-context"

export function useOrder(orderId: string) {
  const { ordersApi } = useServices()
  return useQuery({
    queryKey: ["order", orderId],
    queryFn: () => ordersApi.get(orderId),
    enabled: Boolean(orderId),
  })
}

export function useCreateOrder() {
  const { ordersApi } = useServices()
  return useMutation({ mutationFn: (tableId: string) => ordersApi.create(tableId) })
}

interface AddItemVars {
  productId: string
  quantity: number
  note: string | null
}

export function useAddItem(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: AddItemVars) =>
      ordersApi.addItem(orderId, vars.productId, vars.quantity, vars.note),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["order", orderId] })
    },
  })
}

export function useSendOrder() {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (orderId: string) => ordersApi.send(orderId),
    onSuccess: (order) => {
      void queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["kds-orders"] })
    },
  })
}

interface AdvanceVars {
  orderId: string
  action: OrderAction
}

export function useAdvanceOrder() {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: AdvanceVars) => ordersApi.advance(vars.orderId, vars.action),
    onSuccess: (order) => {
      void queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["kds-orders"] })
    },
  })
}
