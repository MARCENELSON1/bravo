// Namespace `floor`: floor plan (floor-page) and lib/floor-session, floor-filter.
export const floor = {
  title: "Tables",
  subtitle:
    "Live: to serve / to bill / in kitchen. Tap a table to open its order.",
  numberPlaceholder: "Table no.",
  addTable: "Add table",
  searchPlaceholder: "Search table…",
  attention: "Needs attention ({{count}})",
  empty: "No tables yet.",
  emptyManage: "No tables yet — add one above.",
  noMatch: "No matching tables.",
  sinSector: "No sector",
  pax: "· {{count}} pax",
  requestBill: "Request bill",
  // Chips de filtro del salón (§5.2).
  chips: {
    all: "All",
    toServe: "To serve",
    toCharge: "To bill",
    mine: "My tables",
    free: "Free",
  },
  // Etiquetas del estado derivado de la mesa. La CLAVE es el código de estado
  // (FREE/OPEN/…) que devuelve floorView; solo el TEXTO se traduce.
  state: {
    FREE: "Available",
    OPEN: "Open",
    IN_KITCHEN: "In kitchen",
    TO_SERVE: "To serve ⚡",
    SERVED: "Served",
    TO_CHARGE: "To bill",
    CLOSED: "Closed",
  },
  toast: {
    added: "Table added.",
    // Diner's ping from the QR menu (realtime floor.call event).
    callWaiter: "Table {{number}} is calling 🙋",
    bill: "Table {{number}} asked for the check 🧾",
  },
  // Managing/printing the table QR codes (public menu).
  qr: {
    title: "Table QR codes",
    subtitle: "Print one code per table. Guests scan it to see the menu.",
    print: "Print",
    back: "Back",
    tableLabel: "Table {{number}}",
    scanHint: "Scan to see the menu",
    loadError: "We couldn't generate the QR.",
    empty: "No tables yet. Add tables from the floor.",
  },
  errors: {
    openOrder: "We couldn't open the order.",
    requestBill: "We couldn't request the bill.",
    invalidNumber: "Invalid table number.",
    addTable: "We couldn't add the table.",
  },
} as const
