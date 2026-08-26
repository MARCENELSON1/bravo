// Namespace `billing` (P3 gestión). Pantalla de Suscripción (planes/estado/pago).
export const billing = {
  title: "Suscripción",
  back: "Volver",
  activePlan: "Plan activo",
  statusLine: "Estado: {{value}}",
  renewsOn: " · renueva el {{date}}",
  cancelSubscription: "Cancelar suscripción",
  canceling: "Cancelando…",
  cancelConfirm: "¿Seguro que querés cancelar la suscripción?",
  cancelSuccess: "Suscripción cancelada.",
  cancelError: "No pudimos cancelar.",
  chooseIntro:
    "Elegí un plan para activar tu suscripción. El pago es seguro y se procesa en {{gateway}}.",
  noPlans: "Todavía no hay planes disponibles para tu región.",
  subscribe: "Suscribirme",
  redirecting: "Redirigiendo…",
  checkoutError: "No pudimos iniciar el pago.",
  interval: {
    month: "mes",
    year: "año",
  },
  statusLabels: {
    TRIALING: "En prueba",
    ACTIVE: "Activa",
    PAST_DUE: "Pago pendiente",
    INCOMPLETE: "Incompleta",
    CANCELED: "Cancelada",
  },
} as const
