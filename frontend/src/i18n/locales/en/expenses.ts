// Namespace `expenses`: egresos (expenses-page).
export const expenses = {
  title: "Expenses",
  subtitle: "Record and track your cash outflows.",
  new: "New expense",
  // Medios de pago (código = enum, no cambia).
  methodLabels: {
    CASH: "Cash",
    TRANSFER: "Transfer",
    CARD: "Card",
    MERCADOPAGO: "MercadoPago",
  },
  form: {
    description: "A cash outflow (supplier, expense, etc.).",
    amountPlaceholder: "Amount",
    categoryPlaceholder: "Category (e.g. Suppliers)",
    counterpartyPlaceholder: "Counterparty (e.g. South Meat Co.)",
    descriptionPlaceholder: "Description (optional)",
    submit: "Record expense",
    submitting: "Recording…",
    invalidAmount: "Enter a valid amount.",
    success: "Expense recorded.",
    error: "We couldn't record the expense.",
  },
  table: {
    counterparty: "Counterparty",
    category: "Category",
    method: "Method",
    amount: "Amount",
  },
  empty: "You haven't recorded any expenses yet.",
} as const
