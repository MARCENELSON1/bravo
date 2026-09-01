// Carta QR de cara al comensal (ruta pública /carta/:token). UI bilingüe; el
// contenido (nombres de platos) queda en el idioma que cargó el local.
export const publicMenu = {
  loading: "Cargando la carta…",
  menu: "Carta",
  uncategorized: "Otros",
  soldOut: "Agotado",
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
  cart: {
    increase: "Sumar uno",
    decrease: "Quitar uno",
    add: "Agregar",
    review: "Ver pedido",
    title: "Tu pedido",
    empty: "Todavía no elegiste nada.",
    remove: "Quitar",
    send: "Enviar el pedido",
    sending: "Enviando…",
    total: "Total",
  },
  picker: {
    required: "Obligatorio",
    pickOne: "Elegí una opción",
    upTo: "Hasta {{max}}",
    atLeast: "Elegí al menos {{min}}",
    add: "Agregar al pedido",
  },
  sent: {
    title: "¡Pedido enviado!",
    gated: "El mozo lo confirma en un momento y va a la cocina.",
    kitchen: "Ya está en la cocina 🍳",
    again: "Pedir algo más",
  },
  toast: {
    waiterOnTheWay: "El mozo ya viene 🙌",
    billOnTheWay: "Te llevamos la cuenta 🙌",
    failed: "No pudimos avisar. Probá de nuevo.",
    orderFailed: "No pudimos enviar el pedido. Probá de nuevo.",
    orderUnavailable: "Uno de los platos ya no está disponible. Revisá tu pedido.",
  },
  poweredBy: "con Wellnod",
} as const
