import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type {
  CreateIngredientBody,
  CreateSupplierBody,
  PurchaseBody,
  SavePreparationBody,
  SetRecipeBody,
  UpdateIngredientBody,
  WasteBody,
} from "@/api/types-inventory"
import { useServices } from "@/services/services-context"

export function useIngredients() {
  const { inventoryApi } = useServices()
  return useQuery({ queryKey: ["ingredients"], queryFn: () => inventoryApi.listIngredients() })
}

export function useLowStock() {
  const { inventoryApi } = useServices()
  return useQuery({ queryKey: ["low-stock"], queryFn: () => inventoryApi.listLowStock() })
}

export function useFoodCost() {
  const { inventoryApi } = useServices()
  return useQuery({ queryKey: ["food-cost"], queryFn: () => inventoryApi.foodCost() })
}

export function useSuppliers() {
  const { inventoryApi } = useServices()
  return useQuery({ queryKey: ["suppliers"], queryFn: () => inventoryApi.listSuppliers() })
}

// Invalidate everything that depends on stock levels after a movement.
function invalidateStock(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["ingredients"] })
  void queryClient.invalidateQueries({ queryKey: ["low-stock"] })
  void queryClient.invalidateQueries({ queryKey: ["food-cost"] })
}

export function useCreateIngredient() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateIngredientBody) => inventoryApi.createIngredient(body),
    onSuccess: () => invalidateStock(queryClient),
  })
}

export function useUpdateIngredient() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateIngredientBody }) =>
      inventoryApi.updateIngredient(id, body),
    onSuccess: () => invalidateStock(queryClient),
  })
}

export function usePurchase() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: PurchaseBody }) =>
      inventoryApi.purchase(id, body),
    onSuccess: () => invalidateStock(queryClient),
  })
}

export function useWaste() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: WasteBody }) => inventoryApi.waste(id, body),
    onSuccess: () => invalidateStock(queryClient),
  })
}

export function useCreateSupplier() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateSupplierBody) => inventoryApi.createSupplier(body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["suppliers"] }),
  })
}

export function useRecipe(productId: string) {
  const { inventoryApi } = useServices()
  return useQuery({
    queryKey: ["recipe", productId],
    queryFn: () => inventoryApi.getRecipe(productId),
    enabled: Boolean(productId),
  })
}

export function useSetRecipe(productId: string) {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SetRecipeBody) => inventoryApi.setRecipe(productId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["recipe", productId] })
      void queryClient.invalidateQueries({ queryKey: ["food-cost"] })
    },
  })
}

// --- Preparaciones (recetas madre) ------------------------------------------

export function usePreparations() {
  const { inventoryApi } = useServices()
  return useQuery({
    queryKey: ["preparations"],
    queryFn: () => inventoryApi.listPreparations(),
  })
}

// Cambiar una preparación mueve el food cost de los platos que la usan.
function invalidatePreparations(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["preparations"] })
  void queryClient.invalidateQueries({ queryKey: ["food-cost"] })
}

export function useCreatePreparation() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SavePreparationBody) => inventoryApi.createPreparation(body),
    onSuccess: () => invalidatePreparations(queryClient),
  })
}

export function useUpdatePreparation() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: SavePreparationBody }) =>
      inventoryApi.updatePreparation(id, body),
    onSuccess: () => invalidatePreparations(queryClient),
  })
}

export function useDeletePreparation() {
  const { inventoryApi } = useServices()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => inventoryApi.deletePreparation(id),
    onSuccess: () => invalidatePreparations(queryClient),
  })
}
