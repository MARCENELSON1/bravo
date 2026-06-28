import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { Query } from "@tanstack/react-query"

import type { ItemAction, OrderAction } from "@/api/orders-api"
import type { OrderDTO, OrderItemDTO, Station } from "@/api/types-operations"
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
  station: Station
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
          status: "PENDING",
          station: vars.station,
          sent_at: null,
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

export function useRemoveItem(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  const key = ["order", orderId]
  return useMutation<OrderDTO, Error, string, AddItemContext>({
    mutationFn: (itemId) => ordersApi.removeItem(orderId, itemId),
    onMutate: async (itemId) => {
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<OrderDTO>(key)
      if (previous) {
        const item = previous.items.find((i) => i.id === itemId)
        queryClient.setQueryData<OrderDTO>(key, {
          ...previous,
          items: previous.items.filter((i) => i.id !== itemId),
          total_amount:
            previous.total_amount - (item ? item.unit_price_amount * item.quantity : 0),
        })
      }
      return { previous }
    },
    onError: (_error, _itemId, context) => {
      if (context?.previous) queryClient.setQueryData(key, context.previous)
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: key })
    },
  })
}

interface SetQtyVars {
  itemId: string
  quantity: number
}

export function useSetItemQuantity(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  const key = ["order", orderId]
  return useMutation<OrderDTO, Error, SetQtyVars, AddItemContext>({
    mutationFn: (vars) => ordersApi.setItemQuantity(orderId, vars.itemId, vars.quantity),
    onMutate: async (vars) => {
      await queryClient.cancelQueries({ queryKey: key })
      const previous = queryClient.getQueryData<OrderDTO>(key)
      if (previous) {
        let delta = 0
        const items = previous.items.map((i) => {
          if (i.id !== vars.itemId) return i
          delta = (vars.quantity - i.quantity) * i.unit_price_amount
          return { ...i, quantity: vars.quantity }
        })
        queryClient.setQueryData<OrderDTO>(key, {
          ...previous,
          items,
          total_amount: previous.total_amount + delta,
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

export function useTransferOrder(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (tableId: string) => ordersApi.transfer(orderId, tableId),
    onSuccess: (order) => {
      void queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["floor"] })
    },
  })
}

export function useMergeOrders(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (sourceOrderId: string) => ordersApi.merge(orderId, sourceOrderId),
    onSuccess: (order) => {
      void queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["floor"] })
    },
  })
}

// Reabrir una comanda pagada (revierte venta/stock). Refresca la comanda, sus
// pagos, el plano y la caja (el arqueo cambia si después se anula un cobro).
export function useReopenOrder(orderId: string) {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => ordersApi.reopen(orderId),
    onSuccess: (order) => {
      void queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["order-payments", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["floor"] })
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
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

interface AdvanceItemVars {
  orderId: string
  itemId: string
  action: ItemAction
}

// Bump/recall a single item from the per-station KDS board.
export function useAdvanceItem() {
  const { ordersApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: AdvanceItemVars) =>
      ordersApi.advanceItem(vars.orderId, vars.itemId, vars.action),
    onSuccess: (order) => {
      void queryClient.invalidateQueries({ queryKey: ["order", order.id] })
      void queryClient.invalidateQueries({ queryKey: ["kds-orders"] })
    },
  })
}
