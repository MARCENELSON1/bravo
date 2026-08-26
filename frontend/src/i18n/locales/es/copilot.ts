// Namespace `copilot` (P3 gestión): IA Insights / chat del copiloto.
export const copilot = {
  title: "Copiloto",
  subtitle: "Preguntá sobre tu negocio. Te muestro la respuesta y de dónde sale.",
  inputPlaceholder: "¿Cuánto vendí este finde?",
  thinking: "Pensando…",
  ask: "Preguntar",
  // Sugerencias de preguntas.
  examples: [
    "¿Cuánto vendí este mes?",
    "¿Cuáles son mis 5 productos más vendidos?",
    "¿Qué mozo facturó más?",
    "¿Cuántas reservas tengo para mañana?",
  ],
  disabled: "El copiloto todavía no está habilitado en esta cuenta.",
  errorFallback: "No pudimos responder esa pregunta.",
  showSource: "Ver consulta y datos",
  hideSource: "Ocultar consulta y datos",
  noRows: "Sin filas.",
} as const
