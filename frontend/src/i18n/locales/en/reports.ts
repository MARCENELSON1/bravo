// Namespace `reports` (P3 management): Reports screen — period summary, sales by
// day, expenses by category, sales tax to remit, tax filing and top products.
export const reports = {
  title: "Reports",
  // Range selector (the enum lives in lib/finance-range; only the label here).
  ranges: {
    today: "Today",
    week: "This week",
    month: "This month",
    quarter: "Quarter",
  },
  summary: {
    title: "Period summary",
    sales: "Sales",
    collectedNet: "Net collected",
    expenses: "Expenses",
    profit: "Profit",
    avgTicket: "Avg. ticket",
    orders: "Orders",
    error: "We couldn't load the summary.",
  },
  salesByDay: {
    title: "Sales by day",
    empty: "No sales in this period.",
  },
  expensesByCategory: {
    title: "Expenses by category",
    empty: "No expenses in this period.",
    total: "Total",
  },
  taxToRemit: {
    title: "Sales tax collected",
    description:
      "What you collected in tax during the period — to remit to the tax authority (not profit).",
  },
  taxReport: {
    title: "Tax filing (TaxJar)",
    pending_one: "{{count}} sale to report",
    pending_other: "{{count}} sales to report",
    errorsSuffix: " — {{count}} with errors",
    allReported_one: "All reported. {{count}} sale filed.",
    allReported_other: "All reported. {{count}} sales filed.",
    failedNote:
      "Failed ones are retried. If they persist, check that TaxJar is connected in Settings.",
    reportNow: "Report now",
    reporting: "Reporting…",
    upToDate: "Up to date",
    reportPartialError: "Reported {{sent}}. {{failed}} with errors — retry or check TaxJar.",
    reportSuccess: "Reported {{sent}} sales to TaxJar.",
    reportNothing: "There were no sales to report.",
    reportError: "We couldn't report right now. Try again.",
  },
  topProducts: {
    title: "Top products",
    empty: "No product sales in this period.",
    product: "Product",
    units: "Units",
    sales: "Sales",
    margin: "Margin",
  },
} as const
