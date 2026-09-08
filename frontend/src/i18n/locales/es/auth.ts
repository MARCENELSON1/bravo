// Namespace `auth`: la columna de marca de las pantallas de identidad
// (components/auth/auth-layout.tsx).
//
// El título es EL MISMO que el hero de la landing y los tres puntos son sus tres
// grupos de producto (El turno / El negocio / Las decisiones). No es casualidad:
// quien viene de la web tiene que reconocer la promesa con la que entró.
export const auth = {
  brandTitleBefore: "Todo tu restaurante, ",
  brandTitleHighlight: "en una sola app",
  brandSubtitle:
    "Nada de apps sueltas ni de exportar planillas. Todo el local trabaja con los mismos datos.",
  bullets: {
    shift: {
      label: "El turno",
      text: "Mesas, comandas, cocina, caja y facturación, en vivo.",
    },
    business: {
      label: "El negocio",
      text: "Carta con costos, stock, reservas, equipo y finanzas.",
    },
    decisions: {
      label: "Las decisiones",
      text: "El Copiloto responde con tus datos y el Asesor te dice qué hacer.",
    },
  },
} as const
