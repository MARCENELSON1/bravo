// Carta QR de cara al comensal (ruta pública /carta/:token). UI bilingüe; el
// contenido (nombres de platos) queda en el idioma que cargó el local.
export const publicMenu = {
  loading: "Cargando la carta…",
  menu: "Carta",
  uncategorized: "Otros",
  empty: {
    title: "Carta en preparación",
    body: "Todavía no hay platos cargados. Pedile la carta al mozo.",
  },
  invalid: {
    title: "No pudimos abrir la carta",
    body: "Pedile el QR a tu mozo o escaneá de nuevo.",
  },
  error: {
    title: "Algo salió mal",
    body: "No pudimos cargar la carta. Probá de nuevo en un momento.",
  },
  actions: {
    callWaiter: "Llamar al mozo",
    requestBill: "Pedir la cuenta",
  },
  toast: {
    waiterOnTheWay: "El mozo ya viene 🙌",
    billOnTheWay: "Te llevamos la cuenta 🙌",
    failed: "No pudimos avisar. Probá de nuevo.",
  },
  poweredBy: "con Wellnod",
} as const
