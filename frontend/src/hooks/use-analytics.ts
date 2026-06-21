import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { AnalyticsQuery } from "@/api/types-analytics"
import { useServices } from "@/services/services-context"

export function useRevenue(query: AnalyticsQuery) {
  const { analyticsApi } = useServices()
  return useQuery({
    queryKey: ["analytics-revenue", query],
    queryFn: () => analyticsApi.revenue(query),
  })
}

export function usePaymentMix(query: AnalyticsQuery) {
  const { analyticsApi } = useServices()
  return useQuery({
    queryKey: ["analytics-payment-mix", query],
    queryFn: () => analyticsApi.paymentMix(query),
  })
}

export function useProductPerformance(query: AnalyticsQuery) {
  const { analyticsApi } = useServices()
  return useQuery({
    queryKey: ["analytics-products", query],
    queryFn: () => analyticsApi.products(query),
  })
}

export function useRebuildAnalytics() {
  const { analyticsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => analyticsApi.rebuild(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["analytics-revenue"] })
      void queryClient.invalidateQueries({ queryKey: ["analytics-payment-mix"] })
      void queryClient.invalidateQueries({ queryKey: ["analytics-products"] })
    },
  })
}
