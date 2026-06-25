import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { Query } from "@tanstack/react-query"

import type { OrderAction } from "@/api/orders-api"
import type { OrderDTO, OrderItemDTO } from "@/api/types-operations"
import { newId } from "@/lib/ids"
import { useServices } from "@/services/services-context"

type OrderRefetchInterval = number | false | ((query: Query<OrderDTO>) => number | false)

export function useOrder(orderId: string, options?: { refetchInterval?: OrderRefetchInterval }) {
  const { ordersApi } = useServices()
  return useQuery({
    queryKey: ["order", orderId],
    queryFn: () => ordersApi.get(orderId),
    enabled: Boolean(orderId),
    // Used to poll for the webhook-driven transition to PAID after an online charge.
    refetchInterval: options?.refetchInterval ?? false,
  })
}

export function useCreateOrder() {
  const { ordersApi } = useServices()
  // A client-generated id makes the create idempotent (safe to retry/replay).
  return useMutation({ mutationFn: (tableId: string) => ordersApi.create(tableId, newId()) })
}

interface AddItemVars {
  id: string
  productId: string
  name: string
  unitPriceAmount: number
  quantity: number
  note: string | null
}

interface AddItemContext {
  previous: OrderDTO | undefined
}

export function useAddItem(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  const key = ["order", orderId]
  return useMutation<OrderDTO, Error, AddItemVars, AddItemContext>({
    mutationFn: (vars) =>
      ordersApi.addItem(orderId, vars.id, vars.productId, vars.quantity, vars.note),
    // Optimistic: the item appears instantly. The id is the same one the server
    // will persist, so the refetch on settle reconciles with no flicker/dup.
    onMutate: async (vars) => {
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<OrderDTO>(key)
      if (previous) {
        const optimistic: OrderItemDTO = {
          id: vars.id,
          product_id: vars.productId,
          name: vars.name,
          unit_price_amount: vars.unitPriceAmount,
          quantity: vars.quantity,
          note: vars.note,
        }
        queryClient.setQueryData<OrderDTO>(key, {
          ...previous,
          items: [...previous.items, optimistic],
          total_amount: previous.total_amount + vars.unitPriceAmount * vars.quantity,
        })
      }
      return { previous }
    },
    onError: (_error, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(key, context.previous)
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: key })
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
