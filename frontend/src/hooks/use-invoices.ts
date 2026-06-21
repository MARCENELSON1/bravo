import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { IssueInvoiceBody } from "@/api/types-invoicing"
import { useServices } from "@/services/services-context"

export function useInvoices() {
  const { invoicesApi } = useServices()
  return useQuery({ queryKey: ["invoices"], queryFn: () => invoicesApi.list() })
}

export function useOrderInvoice(orderId: string) {
  const { invoicesApi } = useServices()
  return useQuery({
    queryKey: ["order-invoice", orderId],
    queryFn: () => invoicesApi.getForOrder(orderId),
    enabled: Boolean(orderId),
  })
}

export function useIssueInvoice(orderId: string) {
  const { invoicesApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: IssueInvoiceBody) => invoicesApi.issueForOrder(orderId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["order-invoice", orderId] })
      void queryClient.invalidateQueries({ queryKey: ["invoices"] })
    },
  })
}
