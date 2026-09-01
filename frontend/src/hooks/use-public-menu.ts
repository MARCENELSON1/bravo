import { useMutation, useQuery } from "@tanstack/react-query"

import type { CustomerOrderLineDTO } from "@/api/public-menu-api"
import { useServices } from "@/services/services-context"

// Carta pública por token de QR. Sin auth; el token es el scope del tenant.
// `retry: false` → un token inválido no reintenta (muestra el estado enseguida).
export function usePublicMenu(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useQuery({
    queryKey: ["public-menu", token],
    queryFn: () => publicMenuApi.getMenu(token!),
    enabled: !!token,
    retry: false,
  })
}

// "Llamar al mozo": notifica al salón (evento realtime), sin crear orden.
export function useCallWaiter(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useMutation({ mutationFn: () => publicMenuApi.callWaiter(token!) })
}

// "Pedir la cuenta": notifica al salón (evento realtime), sin crear orden.
export function useRequestBill(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useMutation({ mutationFn: () => publicMenuApi.requestBill(token!) })
}

// Autopedido: envía el carrito → crea la comanda. Devuelve si el mozo debe confirmar.
export function useSubmitCustomerOrder(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useMutation({
    mutationFn: (lines: CustomerOrderLineDTO[]) => publicMenuApi.submitOrder(token!, lines),
  })
}

// La cuenta de la mesa (Carta QR F3): total/pagado/saldo + si el local ofrece pago
// online. Solo lectura; el token es el scope.
export function useTableBill(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useQuery({
    queryKey: ["table-bill", token],
    queryFn: () => publicMenuApi.bill(token!),
    enabled: !!token,
    retry: false,
  })
}

// Inicia el pago del saldo de la mesa. El monto lo pone el server; el cliente manda
// propina + clave de idempotencia.
export function usePayTableBill(token: string | undefined) {
  const { publicMenuApi } = useServices()
  return useMutation({
    mutationFn: ({
      tip,
      amount,
      idempotencyKey,
    }: {
      tip: number
      amount: number | null
      idempotencyKey: string
    }) => publicMenuApi.pay(token!, tip, amount, idempotencyKey),
  })
}

// Poll del estado de un pago iniciado (para mostrar "pagado" al confirmar el
// webhook). `refetchInterval` mientras siga PENDING; se corta al confirmar/fallar.
export function usePaymentStatus(token: string | undefined, paymentId: string | null) {
  const { publicMenuApi } = useServices()
  return useQuery({
    queryKey: ["table-payment", token, paymentId],
    queryFn: () => publicMenuApi.paymentStatus(token!, paymentId!),
    enabled: !!token && !!paymentId,
    refetchInterval: (query) =>
      query.state.data && query.state.data.status !== "PENDING" ? false : 2500,
  })
}
