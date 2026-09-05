// Namespace `kds`: pantallas de cocina y barra (kds-page, bar-page, station-board).
export const kds = {
  kitchen: {
    title: "Cocina (KDS)",
    subtitle: "Ítems de cocina en preparación, en vivo.",
  },
  bar: {
    title: "Barra",
    subtitle: "Ítems de barra (café, tragos) en preparación, en vivo.",
  },
  tableLabel: "Mesa {{number}}",
  // Tiempos de servicio: la cocina bumpea el curso entero, no plato por plato.
  onHold: "En espera",
  courses: {
    IMMEDIATE: "Bebidas",
    STARTER: "Entrada",
    MAIN: "Principal",
    DESSERT: "Postre",
  },
  delayed: "demora",
  startPreparing: "Empezar a preparar",
  markReady: "Marcar listo",
  empty: "No hay ítems en {{station}}.",
  errors: {
    itemUpdateFailed: "No se pudo actualizar el ítem.",
    courseUpdateFailed: "No se pudo actualizar el tiempo.",
  },
} as const
