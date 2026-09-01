// Namespace `floor`: plano de salón (floor-page) y lib/floor-session, floor-filter.
export const floor = {
  title: "Mesas",
  subtitle:
    "En vivo: para servir / a cobrar / en cocina. Tocá una mesa para abrir su comanda.",
  numberPlaceholder: "N° de mesa",
  addTable: "Agregar mesa",
  searchPlaceholder: "Buscar mesa…",
  attention: "Requieren atención ({{count}})",
  empty: "No hay mesas todavía.",
  emptyManage: "No hay mesas todavía — agregá una arriba.",
  noMatch: "No hay mesas que coincidan.",
  sinSector: "Sin sector",
  pax: "· {{count}}p",
  requestBill: "Pedir cuenta",
  // Chips de filtro del salón (§5.2).
  chips: {
    all: "Todas",
    toServe: "Para servir",
    toCharge: "A cobrar",
    mine: "Mis mesas",
    free: "Libres",
  },
  // Etiquetas del estado derivado de la mesa. La CLAVE es el código de estado
  // (FREE/OPEN/…) que devuelve floorView; solo el TEXTO se traduce.
  state: {
    FREE: "Libre",
    OPEN: "Abierta",
    IN_KITCHEN: "En cocina",
    TO_SERVE: "Para servir",
    SERVED: "Servida",
    TO_CHARGE: "A cobrar",
    CLOSED: "Cerrada",
  },
  toast: {
    added: "Mesa agregada.",
  },
  errors: {
    openOrder: "No pudimos abrir la comanda.",
    requestBill: "No pudimos pedir la cuenta.",
    invalidNumber: "Número de mesa inválido.",
    addTable: "No pudimos agregar la mesa.",
  },
} as const
