import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

// Las quince áreas del software, en el orden en que se usan durante el día.
// Cada descripción está verificada contra la app: si algo no está construido,
// no se enuncia acá (la única excepción está marcada abajo, en el copiloto).
const FEATURES: readonly Feature[] = [
  {
    id: "floor",
    icon: "floor",
    group: "operation",
    title: "Salón y mesas",
    description:
      "El plano del salón en vivo: qué mesa está libre, cuál está en cocina, cuál tiene el plato para servir y cuál pidió la cuenta. Tocás una y abrís su comanda.",
  },
  {
    id: "orders",
    icon: "orders",
    group: "operation",
    title: "Comandas digitales",
    description:
      "El mozo toma el pedido desde el celular, en la mesa, y llega solo a cocina y barra. Sin papeles ni idas y vueltas.",
  },
  {
    id: "kds",
    icon: "kds",
    group: "operation",
    title: "Cocina y barra",
    description:
      "Cada estación ve lo suyo, ordenado por tiempo y estado, y marca cuando sale. Menos errores y salida más rápida.",
  },
  {
    id: "payments",
    icon: "payments",
    group: "operation",
    title: "Caja, cobros y propinas",
    description:
      "Cobrás por cualquier medio, dividís la cuenta por ítem y repartís las propinas del turno. La caja abre con su fondo y cierra con arqueo.",
  },
  {
    id: "invoices",
    icon: "invoices",
    group: "operation",
    title: "Facturación ARCA",
    description:
      "Emitís la factura electrónica con su CAE en el mismo paso del cobro. Comprobantes al día, sin cargar datos dos veces.",
  },
  {
    id: "reservations",
    icon: "reservations",
    group: "operation",
    title: "Reservas",
    description:
      "La agenda del día por turno: confirmás, sentás en la mesa y registrás los no-shows.",
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
      "Insumos con mínimo por producto y aviso cuando algo se está por acabar. Vender descuenta según la receta.",
  },
  {
    id: "crm",
    icon: "crm",
    group: "management",
    title: "Clientes",
    description:
      "Tu cartera con las visitas de cada uno, para escribirles por WhatsApp y hacerlos volver.",
  },
  {
    id: "team",
    icon: "team",
    group: "management",
    title: "Equipo y permisos",
    description:
      "Invitás a tu gente por email y cada uno entra con su rol —dueño, encargado, mozo, cocina, barra, caja— y ve solo lo que le toca.",
  },
  {
    id: "timeclock",
    icon: "timeclock",
    group: "management",
    title: "Fichaje y personal",
    description:
      "Fichan desde el local con QR o código. De cada uno ves horas y extras para liquidar, mesas atendidas y cuánto facturó.",
  },
  {
    id: "finance",
    icon: "finance",
    group: "management",
    title: "Finanzas y egresos",
    description:
      "Cargá los gastos del local y mirá lo cobrado neto de comisiones. El período se exporta listo para tu contador.",
  },
  {
    id: "reports",
    icon: "reports",
    group: "intelligence",
    title: "Reportes y analítica",
    description:
      "Ventas por día, mix de medios de pago, gastos por rubro y productos más vendidos. En vivo, sin armar planillas.",
  },
  {
    id: "copilot",
    icon: "copilot",
    group: "intelligence",
    title: "Copiloto IA",
    // OJO: "y actúa sobre lo que le pidas" todavía NO está implementado — el
    // copiloto es de solo lectura (backend: allow-list read-only, único endpoint
    // /copilot/ask). Se agregó a pedido, con la función prevista para más adelante.
    description:
      "“¿Cuánto vendí hoy?”, “¿qué plato deja más margen?”. Te responde en lenguaje natural y actúa sobre lo que le pidas.",
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

// El recorrido completo, del alta al cierre y del cierre a la decisión. Cada paso
// cuenta qué hacés Y qué queda hecho solo, que es lo que justifica el software.
const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Cargás tu local una vez",
    description:
      "Mesas y sectores, la carta con sus recetas y costos, y tu equipo con el rol de cada uno. En minutos y sin ayuda técnica.",
  },
  {
    id: "order",
    title: "Abrís la mesa y tomás la comanda",
    description:
      "Desde el celular, en el salón. Cocina y barra reciben lo suyo al instante y avisan cuando el plato sale.",
  },
  {
    id: "charge",
    title: "Cobrás, facturás y cerrás la caja",
    description:
      "Cualquier medio de pago, factura ARCA en el mismo paso, propinas repartidas y arqueo al cierre. El stock se descuenta según la receta.",
  },
  {
    id: "copilot",
    title: "Le preguntás al Copiloto",
    description:
      "“¿Cuánto vendí hoy?”, “¿qué plato deja más margen?”. Responde con tus datos y te muestra de dónde sale cada número.",
  },
  {
    id: "advisor",
    title: "El Asesor te dice qué hacer",
    description:
      "Con tus costos cargados: margen neto, prime cost y punto de equilibrio, más qué conviene hacer hoy y qué esta semana.",
  },
]

// Adapter estático del puerto ContentRepository. Editá los textos acá.
export class StaticContentRepository implements ContentRepository {
  getFeatures(): readonly Feature[] {
    return FEATURES
  }

  getSteps(): readonly Step[] {
    return STEPS
  }

}
