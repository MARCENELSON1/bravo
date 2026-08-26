// Namespace `crm` (P3 management): customers, today's actions and segments.
export const crm = {
  title: "Customers",
  subtitle: "Your customer book. Reach them on WhatsApp with one tap.",
  newCustomer: "New customer",
  cancel: "Cancel",
  save: "Save",
  edit: "Edit",
  delete: "Delete",
  history: "History",
  hide: "Hide",
  whatsapp: "WhatsApp",
  searchPlaceholder: "Search by name or phone…",
  noMatches: "No customers match.",
  empty: "You haven't added any customers yet.",
  editName: "Edit {{name}}",
  confirmDelete: "Delete {{name}}?",
  deleteError: "We couldn't delete the customer.",
  noContactBadge: "Do not contact",
  loading: "Loading…",
  visitWord_one: "visit",
  visitWord_other: "visits",
  spent: "spent",
  daysAgo: " · {{days}}d ago",
  // Messages pre-filled into WhatsApp (visible to the recipient).
  waGreeting: "Hi {{name}}!",
  waWinback: "Hi {{name}}! We miss you — see you soon?",
  historyDetail: {
    noPurchases: "No purchases attributed to them yet. Assign them to an order at checkout.",
    lastVisit: " · last: {{date}}",
    loadError: "We couldn't load the history.",
  },
  form: {
    namePlaceholder: "Name *",
    phonePlaceholder: "Phone (with country code)",
    emailPlaceholder: "Email",
    notesPlaceholder: "Notes",
    noContact: "Do not contact (opt-out) — the WhatsApp button won't be shown",
    nameRequired: "Enter a name.",
    saveError: "We couldn't save the customer.",
  },
  actions: {
    title: "Today's actions",
    subtitle:
      "Customers who used to come often and stopped showing up — the ones with the most at stake.",
    empty:
      "Nothing urgent today. Assign customers to orders to spot the ones going cold.",
    // Sentence with 3 bold values: the fragments wrap each <span>.
    resultA: "Over the last 30 days you contacted ",
    resultB: ", ",
    resultC: " came back and spent ",
    resultD: ".",
    atRisk: "At risk",
    markContacted: "Mark contacted",
    markedSuccess: "Marked as contacted.",
    markError: "We couldn't log the contact.",
  },
  segments: {
    title: "Segments",
    // Sentence with `withPurchases` in bold: coverageA precedes the <span>, coverageB follows it.
    coverageA: "We segmented ",
    coverageB:
      " of {{total}} customers (those with recorded purchases). Assign customers to orders so more show up.",
  },
  // Segment labels (the KEY is the domain enum, unchanged).
  segmentLabels: {
    en_riesgo: "At risk",
    vip: "VIP",
    nuevo: "New",
    recurrente: "Regulars",
    ocasional: "Occasional",
  },
} as const
