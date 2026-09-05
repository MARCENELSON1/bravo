import type { FloorTableDTO, SessionState } from "@/api/types-operations"

// The floor's live view of a table, derived once so the card, the timer, the
// colour and the chips all agree. Prefers the session (the visit) when present;
// falls back to the active order for legacy/sessionless tables (parity).

export type FloorViewState = SessionState | "FREE"

export interface FloorView {
  state: FloorViewState
  label: string
  // ISO timestamp the current state began → the timer measures "how long in
  // THIS state", not since the table opened. null → no timer.
  since: string | null
  // Needs a human now (para servir / a cobrar) → the card asks for attention.
  attention: boolean
  pax: number | null
  waiterId: string | null
  waiterName: string | null
}

const _LABELS: Record<FloorViewState, string> = {
  FREE: "Libre",
  OPEN: "Abierta",
  IN_KITCHEN: "En cocina",
  TO_SERVE: "Para servir",
  SERVED: "Servida",
  TO_CHARGE: "A cobrar",
  CLOSED: "Cerrada",
}

// Map a sessionless active order's status to a floor state (parity fallback).
function stateFromOrder(status: string): SessionState {
  switch (status) {
    case "OPEN":
      return "OPEN"
    case "SENT":
    case "PREPARING":
      return "IN_KITCHEN"
    case "READY":
      return "TO_SERVE"
    case "SERVED":
      return "SERVED"
    default:
      return "OPEN"
  }
}

export function floorView(table: FloorTableDTO): FloorView {
  const s = table.session
  if (s) {
    return {
      state: s.state,
      label: _LABELS[s.state] ?? s.state,
      since: s.state_since,
      attention: s.state === "TO_SERVE" || s.state === "TO_CHARGE",
      pax: s.pax,
      waiterId: s.waiter_id,
      waiterName: s.waiter_name,
    }
  }
  const order = table.active_order
  if (!order) {
    return {
      state: "FREE",
      label: _LABELS.FREE,
      since: null,
      attention: false,
      pax: null,
      waiterId: null,
      waiterName: null,
    }
  }
  const state = stateFromOrder(order.status)
  return {
    state,
    label: _LABELS[state],
    since: order.created_at,
    attention: state === "TO_SERVE",
    pax: null,
    waiterId: order.waiter_id,
    waiterName: null,
  }
}
