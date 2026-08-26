// Namespace `crm` (P3 gestión): clientes, acciones para hoy y segmentos.
export const crm = {
  title: "Clientes",
  subtitle: "Tu cartera de clientes. Contactalos por WhatsApp con un toque.",
  newCustomer: "Nuevo cliente",
  cancel: "Cancelar",
  save: "Guardar",
  edit: "Editar",
  delete: "Borrar",
  history: "Historial",
  hide: "Ocultar",
  whatsapp: "WhatsApp",
  searchPlaceholder: "Buscar por nombre o teléfono…",
  noMatches: "No hay clientes que coincidan.",
  empty: "Todavía no cargaste clientes.",
  editName: "Editar {{name}}",
  confirmDelete: "¿Borrar a {{name}}?",
  deleteError: "No pudimos borrar el cliente.",
  noContactBadge: "No contactar",
  loading: "Cargando…",
  visitWord_one: "visita",
  visitWord_other: "visitas",
  spent: "gastados",
  daysAgo: " · hace {{days}}d",
  // Mensajes que se pre-cargan en WhatsApp (visibles para el destinatario).
  waGreeting: "Hola {{name}}!",
  waWinback: "Hola {{name}}! Te extrañamos, ¿te esperamos pronto?",
  historyDetail: {
    noPurchases: "Todavía no le atribuiste ninguna compra. Asignalo a una comanda al cobrar.",
    lastVisit: " · última: {{date}}",
    loadError: "No pudimos cargar el historial.",
  },
  form: {
    namePlaceholder: "Nombre *",
    phonePlaceholder: "Teléfono (con código país)",
    emailPlaceholder: "Email",
    notesPlaceholder: "Notas",
    noContact: "No contactar (opt-out) — no se ofrece el botón de WhatsApp",
    nameRequired: "Poné un nombre.",
    saveError: "No pudimos guardar el cliente.",
  },
  actions: {
    title: "Acciones para hoy",
    subtitle:
      "Clientes que venían seguido y dejaron de aparecer — los de mayor plata en juego.",
    empty:
      "Nada urgente hoy. Atribuí clientes a las comandas para detectar a los que se enfrían.",
    // Frase con 3 valores en negrita: los fragmentos rodean cada <span>.
    resultA: "En los últimos 30 días contactaste ",
    resultB: ", volvieron ",
    resultC: " y gastaron ",
    resultD: ".",
    atRisk: "En riesgo",
    markContacted: "Marcar contactado",
    markedSuccess: "Marcado como contactado.",
    markError: "No pudimos registrar el contacto.",
  },
  segments: {
    title: "Segmentos",
    // Frase con `withPurchases` en negrita: coverageA precede al <span>, coverageB lo sigue.
    coverageA: "Segmentamos ",
    coverageB:
      " de {{total}} clientes (los que tienen compras registradas). Atribuí clientes a las comandas para que entren más.",
  },
  // Etiquetas de segmento (la KEY es el enum del dominio, no cambia).
  segmentLabels: {
    en_riesgo: "En riesgo",
    vip: "VIP",
    nuevo: "Nuevos",
    recurrente: "Recurrentes",
    ocasional: "Ocasionales",
  },
} as const
