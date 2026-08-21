import type { Faq } from "@/domain/entities/faq"
import type { Feature } from "@/domain/entities/feature"
import type { Integration } from "@/domain/entities/integration"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

const FEATURES: readonly Feature[] = [
  {
    id: "orders",
    icon: "orders",
    title: "Comandas digitales",
    description:
      "El mozo toma el pedido desde el celular y llega solo a cocina y barra. Sin papeles ni idas y vueltas.",
  },
  {
    id: "payments",
    icon: "payments",
    title: "Cobros y facturación AFIP",
    description:
      "Cobrá con MercadoPago y emití la factura electrónica en el mismo paso. AFIP nativo, sin planillas.",
  },
  {
    id: "copilot",
    icon: "copilot",
    title: "Copiloto IA en español",
    description:
      "Preguntale a tu negocio en lenguaje natural: “¿cuánto vendí hoy?”, “¿qué plato deja más margen?”.",
  },
  {
    id: "kds",
    icon: "kds",
    title: "Pantalla de cocina (KDS)",
    description:
      "La cocina ve los pedidos ordenados por tiempo y estado. Menos errores, salida más rápida.",
  },
  {
    id: "timeclock",
    icon: "timeclock",
    title: "Fichaje de empleados",
    description:
      "Entradas y salidas del personal desde el local, con reportes de horas listos para liquidar.",
  },
  {
    id: "reports",
    icon: "reports",
    title: "Reportes en tiempo real",
    description:
      "Ventas, caja y márgenes al instante, en pesos. Tomá decisiones con datos, no con la intuición.",
  },
]

const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Cargá tu menú y tus mesas",
    description:
      "Configurás productos, precios y el salón una sola vez. En minutos, sin ayuda técnica.",
  },
  {
    id: "order",
    title: "El mozo toma la comanda",
    description: "Desde el celular, en la mesa. Sin papelitos ni gritos a la cocina.",
  },
  {
    id: "kitchen",
    title: "Cocina y barra la reciben al instante",
    description: "El pedido aparece en el KDS ordenado por tiempo. Se prepara y sale más rápido.",
  },
  {
    id: "charge",
    title: "Cobrás, facturás y medís",
    description:
      "Cobro con MercadoPago, factura AFIP en el mismo paso y el reporte del día actualizado.",
  },
]

const INTEGRATIONS: readonly Integration[] = [
  { id: "mercadopago", name: "MercadoPago", description: "Cobros y QR" },
  { id: "afip", name: "AFIP / ARCA", description: "Factura electrónica" },
  { id: "printers", name: "Impresoras", description: "Comandas y tickets" },
  { id: "whatsapp", name: "WhatsApp", description: "Avisos y pedidos" },
  { id: "point", name: "Point", description: "Terminal de pago" },
  { id: "sheets", name: "Exportá a Excel", description: "Reportes y datos" },
]

const FAQS: readonly Faq[] = [
  {
    id: "hardware",
    question: "¿Necesito comprar hardware especial?",
    answer:
      "No. Wellnod funciona en los celulares, tablets o computadoras que ya tenés. Si querés, se integra con impresoras de comandas.",
  },
  {
    id: "afip",
    question: "¿Emite factura electrónica de AFIP?",
    answer:
      "Sí. La facturación AFIP es nativa: cobrás y facturás en el mismo flujo, sin cargar datos dos veces.",
  },
  {
    id: "trial",
    question: "¿Puedo probarlo gratis?",
    answer:
      "Sí. El plan Emprendé es gratis para empezar, y podés pasar a Profesional cuando lo necesites. Sin tarjeta para arrancar.",
  },
  {
    id: "multi",
    question: "¿Sirve si tengo más de un local?",
    answer:
      "Sí. El plan Multi-local te da un panel consolidado de todos tus puntos de venta con roles y permisos por local.",
  },
  {
    id: "copilot",
    question: "¿Qué es el copiloto de IA?",
    answer:
      "Es un asistente que responde en español sobre tu negocio: ventas, márgenes, stock y más, sin que tengas que armar reportes.",
  },
  {
    id: "data",
    question: "¿Mis datos están seguros?",
    answer:
      "Cada local trabaja con sus datos aislados. La información se resguarda con cifrado y buenas prácticas de seguridad.",
  },
]

// Adapter estático del puerto ContentRepository. Editá los textos acá.
export class StaticContentRepository implements ContentRepository {
  async getFeatures(): Promise<readonly Feature[]> {
    return FEATURES
  }

  async getSteps(): Promise<readonly Step[]> {
    return STEPS
  }

  async getIntegrations(): Promise<readonly Integration[]> {
    return INTEGRATIONS
  }

  async getFaqs(): Promise<readonly Faq[]> {
    return FAQS
  }
}
