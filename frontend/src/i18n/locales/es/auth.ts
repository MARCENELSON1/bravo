// Namespace `auth`: la columna de marca de las pantallas de identidad
// (components/auth/auth-shell.tsx).
//
// El título es EL MISMO que el hero de la landing y los tres puntos son sus tres
// grupos de producto, con las MISMAS áreas adentro de cada uno (ver el listado en
// landing/src/infrastructure/repositories/static-content-repository.ts). No es
// casualidad: quien viene de la web tiene que reconocer la promesa con la que entró,
// y si acá faltan áreas parece un producto más chico que el que le mostraron.
//
// Del Copiloto se dice lo que hace hoy —responder con tus datos—, no lo que va a
// hacer. Prometerle a alguien que está creando su cuenta algo que todavía no existe
// se paga caro cinco minutos después.
export const auth = {
  brandTitleBefore: "Todo tu restaurante, ",
  brandTitleHighlight: "en una sola app",
  brandSubtitle:
    "Nada de apps sueltas ni de exportar planillas. Todo el local trabaja con los mismos datos.",
  bullets: {
    shift: {
      label: "El turno",
      text: "Mesas, comandas, cocina y barra, caja, facturación y reservas: el servicio entero, en vivo.",
    },
    business: {
      label: "El negocio",
      text: "Carta con sus costos, stock, clientes, equipo, fichaje y finanzas, en un solo lugar.",
    },
    decisions: {
      label: "Las decisiones",
      text: "Reportes al día, un Copiloto que responde con tus datos y un Asesor que te dice qué hacer.",
    },
  },
} as const
