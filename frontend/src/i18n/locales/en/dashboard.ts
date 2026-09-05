// Namespace `dashboard`: Home screen and its helpers (daily verdict, alerts,
// dining-room and register snapshots).
export const dashboard = {
  // Header
  greeting: "Good morning",
  greetingNamed: "Good morning, {{name}}",
  weekdays: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
  months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  todayFormat: "{{weekday}}, {{month}} {{day}}, {{year}}",

  // Generic states
  loading: "Loading…",

  // Level 1 — today's profit
  todayProfit: "Your profit today",
  profitTentative: "Tentative — you haven't logged any expenses today yet.",
  feesDeducted: "We already deducted {{amount}} in card / MercadoPago fees.",
  verdict: {
    good: "Good day{{vs}}",
    ok: "Average day{{vs}}",
    bad: "Day to review{{vs}}",
    vsMore: " — {{pct}}% more than yesterday",
    vsLess: " — {{pct}}% less than yesterday",
  },

  // Level 2 — the 3 numbers that explain it
  billedToday: "Billed today",
  paymentsCount: "{{n}} payments",
  spentToday: "Spent today",
  expensesRegistered: "Expenses logged",
  marginToday: "Your margin today",
  loadExpensesForMargin: "Log your expenses to see your real margin",
  marginExplain: "Of every $100, ${{margin}} is profit",
  noSalesYet: "No sales yet",

  // Level 3 — payments by channel
  channelsTitle: "Today's payments by channel",
  channelsSubtitle: "Gross amounts (we haven't deducted Mercado Pago / card fees yet).",
  noPaymentsToday: "No payments yet today.",
  methods: {
    CASH: "Cash",
    CARD: "Card",
    TRANSFER: "Transfer",
    MERCADOPAGO: "MercadoPago",
    QR: "QR",
  },

  // Level 4 — alert of the day
  attentionToday: "Attention today",

  // Level 5 — month progress
  revenue7dTitle: "Revenue, last 7 days",
  totalSuffix: "{{amount}} total",
  monthClose: "Month close",
  onTrackToClose: "If you keep this up, you'll close at",
  dayOfMonth: "Day {{elapsed}} of {{total}}",
  calculating: "Calculating…",
  notEnoughData: "Not enough data to forecast.",
  viewFinance: "View Finance",
  noSales7d: "No sales in the last 7 days.",

  // Level 7 — task for tomorrow
  tomorrowTaskTitle: "Your task for tomorrow",
  gotIt: "Got it",

  // Floating button
  registerExpense: "Log expense",

  // Dining-room snapshot
  salon: {
    title: "Dining room",
    viewTables: "View tables →",
    empty: "No tables set up.",
    occupied: "occupied",
    free: "free",
    toServe: "to serve",
    toCharge: "to charge",
  },

  // Register snapshot
  cash: {
    title: "Register",
    goToRegister: "Go to register →",
    openRegister: "Open register →",
    open: "Register open",
    expected: "Expected:",
    closedHint: "Register not opened. Open it to charge and reconcile the shift.",
  },

  // Needs your attention + operational alerts
  requiresAttention: {
    title: "Needs your attention",
    allClear: "Nothing urgent right now. All clear ✓",
  },
  alerts: {
    toServe_one: "{{count}} table to serve",
    toServe_other: "{{count}} tables to serve",
    toCharge_one: "{{count}} table to charge",
    toCharge_other: "{{count}} tables to charge",
    cashClosed: "Register not opened",
    lowStock_one: "{{count}} item to restock",
    lowStock_other: "{{count}} items to restock",
    atRisk_one: "{{count}} customer at risk",
    atRisk_other: "{{count}} customers at risk",
  },
} as const
