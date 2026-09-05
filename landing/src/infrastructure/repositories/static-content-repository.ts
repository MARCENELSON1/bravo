import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

const FEATURES: readonly Feature[] = [
  {
    id: "orders",
    icon: "orders",
    group: "operation",
    title: "Comandas digitales",
    description:
      "El mozo toma el pedido desde el celular y llega solo a cocina y barra. Sin papeles ni idas y vueltas.",
  },
  {
    id: "kds",
    icon: "kds",
    group: "operation",
    title: "Cocina y barra",
    description:
      "Cada estación ve lo suyo, ordenado por tiempo y estado. Menos errores y salida más rápida.",
  },
  {
    id: "payments",
    icon: "payments",
    group: "operation",
    title: "Caja, cobros y propinas",
    description:
      "Abrís y cerrás la caja con su arqueo, cobrás por cualquier medio y repartís las propinas del turno.",
  },
  {
    id: "invoices",
    icon: "invoices",
    group: "management",
    title: "Facturación ARCA",
    description:
      "Emití la factura electrónica en el mismo paso del cobro. Comprobantes al día, sin cargar datos dos veces.",
  },
  {
    id: "menu",
    icon: "menu",
    group: "management",
    title: "Carta y recetas",
    description:
      "Cargá productos, precios y recetas. Wellnod calcula el costo de cada plato y cuánto margen te deja.",
  },
  {
    id: "inventory",
    icon: "inventory",
    group: "management",
    title: "Stock y proveedores",
    description:
      "Insumos con mínimo por producto, aviso cuando algo se está por acabar y tus proveedores a mano.",
  },
  {
    id: "reservations",
    icon: "reservations",
    group: "management",
    title: "Reservas y clientes",
    description:
      "La agenda del turno con confirmaciones y no-shows, y tu cartera de clientes para volver a contactarlos.",
  },
  {
    id: "timeclock",
    icon: "timeclock",
    group: "management",
    title: "Fichaje y personal",
    description:
      "Entradas y salidas del equipo desde el local, con las horas de cada uno listas para liquidar.",
  },
  {
    id: "finance",
    icon: "finance",
    group: "management",
    title: "Finanzas y egresos",
    description:
      "Cargá los gastos del local y mirá lo cobrado neto de comisiones. Lo que entra y lo que sale, junto.",
  },
  {
    id: "reports",
    icon: "reports",
    group: "intelligence",
    title: "Reportes y analítica",
    description:
      "Ventas por día, mix de medios de pago y productos más vendidos. En vivo, sin armar planillas.",
  },
  {
    id: "copilot",
    icon: "copilot",
    group: "intelligence",
    title: "Copiloto IA",
    description:
      "Preguntale a tu negocio en lenguaje natural: “¿cuánto vendí hoy?”, “¿qué plato deja más margen?”.",
  },
  {
    id: "advisor",
    icon: "advisor",
    group: "intelligence",
    title: "Asesor",
    description:
      "Margen neto, prime cost y punto de equilibrio, con diagnósticos de qué hacer hoy y qué esta semana.",
  },
]

const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Cargás tu local una vez",
    description: "Menú, precios, mesas y equipo. En minutos, sin ayuda técnica.",
  },
  {
    id: "order",
    title: "El mozo toma la comanda",
    description:
      "Desde el celular, en la mesa. Llega sola a cocina y barra, ordenada por tiempo.",
  },
  {
    id: "charge",
    title: "Cobrás y facturás",
    description:
      "Cobro, factura ARCA y el cierre de caja con su arqueo. Todo en el mismo flujo.",
  },
  {
    id: "copilot",
    title: "Le preguntás al Copiloto",
    description:
      "“¿Cuánto vendí hoy?”, “¿qué plato deja más margen?”. Responde con tus datos reales.",
  },
  {
    id: "advisor",
    title: "El Asesor te dice qué hacer",
    description:
      "Margen neto, prime cost y punto de equilibrio, con diagnósticos para hoy y para esta semana.",
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

}
