// Namespace `finance` (P3 management). Finances screen + management cards.
export const finance = {
  title: "Finances",
  loadError: "We couldn't load your finances.",
  loading: "Loading…",
  ranges: {
    today: "Today",
    week: "This week",
    month: "This month",
    quarter: "Quarter",
  },
  kpiLabels: {
    prime_cost: "Prime Cost",
    food_cost: "Food Cost",
    labor_cost: "Labor cost",
    waste: "Waste",
    net_margin: "Net margin",
    gross_margin: "Gross margin",
    break_even: "Break-even",
    revpash: "RevPASH",
    inventory_turnover: "Inventory turnover",
  },
  statusActions: {
    healthy: "Maintain",
    warn: "Review",
    alert: "Act",
    neutral: "—",
  },
  healthyRange: "healthy {{low}}–{{high}}",
  healthyMax: "healthy < {{high}}",
  configureCosts:
    "Enter your fixed costs (labor and others) in the Advisor so net margin and prime cost are accurate.",
  hero: {
    netProfit: "Your net profit for the period",
    vsPrevious: "vs. previous period",
    projectionPrefix: "At this pace, you'll close at",
    projectionDays: "({{elapsed}}/{{total}} days)",
  },
  commissions: {
    label: "Payment processing fees (gateways)",
    netCollected: "Collected net of fees:",
  },
  diagnostics: {
    title: "Diagnostics",
  },
  productMargins: {
    title: "Contribution margin by product",
    product: "Product",
    unitsMargin: "Units · Margin",
    noLines: "No lines in the period.",
  },
  exports: {
    title: "Export for your accountant",
    description:
      "Download the period's data as CSV (Excel-ready). Opens with accents and semicolon-separated.",
    error: "We couldn't generate the file.",
    items: {
      sales: { label: "Sales (CSV)", filename: "sales-by-day.csv" },
      expenses: { label: "Expenses (CSV)", filename: "expenses.csv" },
      vat_sales: { label: "Sales Tax Book (CSV)", filename: "sales-tax-book.csv" },
    },
  },
  commissionRates: {
    title: "Fees by payment method",
    descPre:
      "What the gateway keeps from each payment. With this, Home shows you your",
    descEm: "real",
    descPost: "profit after fees. Empty = 0%.",
    invalid: "Invalid fee (between 0 and 100%).",
    saved: "Fees saved.",
    saveError: "We couldn't save the fees.",
    save: "Save fees",
    saving: "Saving…",
  },
  paymentMethods: {
    CARD: "Card",
    MERCADOPAGO: "MercadoPago",
    QR: "QR",
  },
  expenseChanges: {
    title: "The 3 expenses that changed the most",
    empty: "No significant changes vs. the previous period.",
    legend: "▲ up vs. previous period · ▼ down",
  },
  expenseDonut: {
    title: "Expense distribution",
    empty: "No expenses recorded in the period.",
    other: "Other",
  },
  recentMovements: {
    title: "Recent movements",
    loading: "Loading…",
    empty: "No movements in the period.",
    income: "Payment",
    expense: "Expense",
  },
} as const
