import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { AnalyticsQuery } from "@/api/types-analytics"
import type { ModifierGroupInput, Station } from "@/api/types-operations"
import { useServices } from "@/services/services-context"

export function useProducts() {
  const { productsApi } = useServices()
  return useQuery({ queryKey: ["products"], queryFn: () => productsApi.list() })
}

// --- Productos v2 Tanda B: precios vs inflación + histórico + rotación --------

export function usePricingInsights() {
  const { productsApi } = useServices()
  return useQuery({
    queryKey: ["products", "pricing"],
    queryFn: () => productsApi.pricing(),
  })
}

export function useProductPriceHistory(productId: string | null) {
  const { productsApi } = useServices()
  return useQuery({
    queryKey: ["products", "price-history", productId],
    queryFn: () => productsApi.priceHistory(productId!),
    enabled: productId != null,
  })
}

// --- Carta QR F2 D/E: modificadores ------------------------------------------

export function useProductModifiers(productId: string | null) {
  const { productsApi } = useServices()
  return useQuery({
    queryKey: ["products", "modifiers", productId],
    queryFn: () => productsApi.modifiers(productId!),
    enabled: productId != null,
  })
}

export function useSetProductModifiers() {
  const { productsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: { productId: string; groups: ModifierGroupInput[] }) =>
      productsApi.setModifiers(vars.productId, vars.groups),
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({
        queryKey: ["products", "modifiers", vars.productId],
      })
    },
  })
}

export function useProductRotation(query: AnalyticsQuery = {}) {
  const { productsApi } = useServices()
  return useQuery({
    queryKey: ["products", "rotation", query.from ?? null, query.to ?? null],
    queryFn: () => productsApi.rotation(query),
  })
}

export function useUpdateProductPrice() {
  const { productsApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: { productId: string; priceAmount: number }) =>
      productsApi.updatePrice(vars.productId, vars.priceAmount),
    onSuccess: () => {
      // Prefijo "products" cubre catálogo + pricing + rotación + histórico.
      void queryClient.invalidateQueries({ queryKey: ["products"] })
    },
  })
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
