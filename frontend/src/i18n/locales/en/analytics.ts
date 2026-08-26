// Namespace `analytics` (P3 management): analytics screen (KPIs, payment method
// mix, top-selling products).
export const analytics = {
  title: "Analytics",
  description:
    "Your numbers in dollars, read from the canonical model. Leave the dates blank to see everything.",
  dateFrom: "From",
  dateTo: "To",
  kpis: {
    sales: "Sales",
    collected: "Collected",
    expenses: "Expenses",
    grossMargin: "Gross margin",
    grossMarginHint: "Sales − food cost",
    averageTicket: "Average ticket",
    foodCost: "Food cost",
  },
  // Cantidad de comandas (glosario: Comanda = Order).
  ordersCount_one: "{{count}} order",
  ordersCount_other: "{{count}} orders",
  paymentMix: {
    title: "Payment method mix",
    hint: "Gross amounts (before gateway fees). Amounts collected net of fees are shown in Finance and on Home.",
    method: "Method",
    type: "Type",
    operations: "Operations",
    amount: "Amount",
    empty: "No payments in this period.",
  },
  topProducts: {
    title: "Top-selling products",
    product: "Product",
    units: "Units",
    sales: "Sales",
    foodCost: "Food cost",
    margin: "Margin",
    empty: "No sales in this period.",
  },
  // Medios de pago (código = enum, no cambia).
  methodLabels: {
    CASH: "Cash",
    CARD: "Card",
    TRANSFER: "Transfer",
    MERCADOPAGO: "MercadoPago",
    QR: "QR",
  },
  // Dirección del movimiento (código = enum, no cambia).
  directionLabels: {
    INFLOW: "Inflow",
    OUTFLOW: "Outflow",
  },
} as const
