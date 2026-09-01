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
    TO_SERVE: "Para servir ⚡",
    SERVED: "Servida",
    TO_CHARGE: "A cobrar",
    CLOSED: "Cerrada",
  },
  toast: {
    added: "Mesa agregada.",
    // Aviso del comensal desde la carta QR (evento realtime floor.call).
    callWaiter: "Mesa {{number}} te llama 🙋",
    bill: "Mesa {{number}} pide la cuenta 🧾",
  },
  // Gestión/impresión de los QR de mesa (carta pública).
  qr: {
    title: "QR de las mesas",
    subtitle: "Imprimí un código por mesa. El cliente lo escanea y ve la carta.",
    print: "Imprimir",
    back: "Volver",
    tableLabel: "Mesa {{number}}",
    scanHint: "Escaneá para ver la carta",
    loadError: "No pudimos generar el QR.",
    empty: "No hay mesas todavía. Agregá mesas en el salón.",
    selfOrder: {
      title: "Autopedido",
      subtitle: "Dejá que el comensal cargue su pedido desde el QR.",
      enable: "Habilitar autopedido por QR",
      requireConfirmation: "Requiere que el mozo confirme el pedido",
      requireConfirmationHint:
        "Recomendado: el pedido llega a la comanda y el mozo lo confirma (marcha a cocina).",
      saved: "Config guardada",
      saveFailed: "No pudimos guardar. Probá de nuevo.",
    },
  },
  errors: {
    openOrder: "No pudimos abrir la comanda.",
    requestBill: "No pudimos pedir la cuenta.",
    invalidNumber: "Número de mesa inválido.",
    addTable: "No pudimos agregar la mesa.",
  },
} as const
