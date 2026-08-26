// Namespace `dashboard`: pantalla de Inicio (Home) y sus helpers (veredicto del
// día, alertas, snapshots de salón y caja).
export const dashboard = {
  // Encabezado
  greeting: "Buen día",
  greetingNamed: "Buen día, {{name}}",
  weekdays: ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
  months: ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
  todayFormat: "{{weekday}}, {{day}} {{month}} {{year}}",

  // Estados genéricos
  loading: "Cargando…",

  // Nivel 1 — ganancia del día
  todayProfit: "Tu ganancia de hoy",
  profitTentative: "Provisorio — todavía no cargaste egresos hoy.",
  feesDeducted: "Ya restamos {{amount}} de comisiones de tarjeta / MercadoPago.",
  verdict: {
    good: "Buen día{{vs}}",
    ok: "Día normal{{vs}}",
    bad: "Día para revisar{{vs}}",
    vsMore: " — {{pct}}% más que ayer",
    vsLess: " — {{pct}}% menos que ayer",
  },

  // Nivel 2 — los 3 números que lo explican
  billedToday: "Facturaste hoy",
  paymentsCount: "{{n}} cobros",
  spentToday: "Gastaste hoy",
  expensesRegistered: "Egresos registrados",
  marginToday: "Tu margen hoy",
  loadExpensesForMargin: "Cargá tus egresos para saber el margen real",
  marginExplain: "De cada $100, ${{margin}} son ganancia",
  noSalesYet: "Sin ventas aún",

  // Nivel 3 — cobros por canal
  channelsTitle: "Cobros de hoy por canal",
  channelsSubtitle: "Montos brutos (aún no descontamos comisiones de Mercado Pago / tarjeta).",
  noPaymentsToday: "Todavía no hubo cobros hoy.",
  methods: {
    CASH: "Efectivo",
    CARD: "Tarjeta",
    TRANSFER: "Transferencia",
    MERCADOPAGO: "MercadoPago",
    QR: "QR",
  },

  // Nivel 4 — alerta del día
  attentionToday: "Atención hoy",

  // Nivel 5 — progreso del mes
  revenue7dTitle: "Facturación últimos 7 días",
  totalSuffix: "{{amount}} total",
  monthClose: "Cierre del mes",
  onTrackToClose: "Si seguís así, cerrás en",
  dayOfMonth: "Día {{elapsed}} de {{total}}",
  calculating: "Calculando…",
  notEnoughData: "Sin datos suficientes para proyectar.",
  viewFinance: "Ver Finanzas",
  noSales7d: "Sin ventas en los últimos 7 días.",

  // Nivel 7 — tarea para mañana
  tomorrowTaskTitle: "Tu tarea para mañana",
  gotIt: "Entendido",

  // Botón flotante
  registerExpense: "Registrar egreso",

  // Snapshot del salón
  salon: {
    title: "Salón",
    viewTables: "Ver mesas →",
    empty: "No hay mesas cargadas.",
    occupied: "ocupadas",
    free: "libres",
    toServe: "para servir ⚡",
    toCharge: "para cobrar",
  },

  // Snapshot de la caja
  cash: {
    title: "Caja",
    goToRegister: "Ir a la caja →",
    openRegister: "Abrir caja →",
    open: "Caja abierta",
    expected: "Esperado:",
    closedHint: "Caja sin abrir. Abrila para cobrar y hacer el arqueo del turno.",
  },

  // Requiere tu atención + alertas operativas
  requiresAttention: {
    title: "Requiere tu atención",
    allClear: "Nada urgente por ahora. Todo en orden ✓",
  },
  alerts: {
    toServe_one: "{{count}} mesa para servir ⚡",
    toServe_other: "{{count}} mesas para servir ⚡",
    toCharge_one: "{{count}} mesa para cobrar",
    toCharge_other: "{{count}} mesas para cobrar",
    cashClosed: "Caja sin abrir",
    lowStock_one: "{{count}} insumo por reponer",
    lowStock_other: "{{count}} insumos por reponer",
    atRisk_one: "{{count}} cliente en riesgo",
    atRisk_other: "{{count}} clientes en riesgo",
  },
} as const
