import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { RegisterExpenseBody, RegisterPaymentBody } from "@/api/types-operations"
import { useServices } from "@/services/services-context"

export function useOrderPayments(orderId: string) {
  const { paymentsApi } = useServices()
  return useQuery({
    queryKey: ["order-payments", orderId],
    queryFn: () => paymentsApi.listForOrder(orderId),
    enabled: Boolean(orderId),
  })
}

export function useRegisterPayment(orderId: string) {
  const { paymentsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: RegisterPaymentBody) => paymentsApi.registerForOrder(orderId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["order", orderId] })
      void queryClient.invalidateQueries({ queryKey: ["order-payments", orderId] })
    },
  })
}

export function useRefundPayment(orderId: string) {
  const { paymentsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (paymentId: string) => paymentsApi.refund(paymentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["order", orderId] })
      void queryClient.invalidateQueries({ queryKey: ["order-payments", orderId] })
      void queryClient.invalidateQueries({ queryKey: ["cash-session"] })
    },
  })
}

export function useExpenses() {
  const { paymentsApi } = useServices()
  return useQuery({ queryKey: ["expenses"], queryFn: () => paymentsApi.listExpenses() })
}

export function useRegisterExpense() {
  const { paymentsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: RegisterExpenseBody) => paymentsApi.registerExpense(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["expenses"] })
    },
  })
}
