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
// El recorrido completo, encadenado: cada paso usa lo que dejó el anterior. La carga
// alimenta la carta, la carta alimenta la comanda, la comanda alimenta el cobro, el
// cobro alimenta los datos y los datos alimentan la decisión.
//
// OJO: dos cosas de este texto NO están implementadas todavía.
//   - Que el Copiloto ACCIONE (destacar un plato, tocar un precio). Hoy es de solo
//     lectura: allow-list read-only en el backend y un único endpoint /copilot/ask.
//   - La CARTA PARA EL CLIENTE, con sus recomendaciones y el detalle de cada plato.
//     No hay ninguna pantalla pública de carta; lo que existe es el catálogo interno
//     que usa el mozo, y las recomendaciones no están construidas en ningún lado.
//   - La MIGRACIÓN desde otro sistema. En la app solo hay exportación a CSV para el
//     contador (finance); no existe ninguna importación.
// Las dos se agregaron a pedido, con la función prevista para más adelante — la misma
// decisión que ya se tomó en la tarjeta del copiloto, más arriba.
const STEPS: readonly Step[] = [
  {
    id: "setup",
    title: "Arrancás en minutos, no en semanas",
    description:
      "Se carga una sola vez toda la información requerida del local: mesas, carta con el costo de cada plato, proveedores, etc. Y si venís de otro sistema, migrás lo que ya tenías. Sin instalar nada: esa carga es la base, todo lo que sigue se alimenta de ahí.",
  },
  {
    id: "order",
    title: "Una sola carta, dos pantallas",
    description:
      "El mozo toma el pedido desde la comandera, o los comensales eligen lo que van a pedir desde la misma carta, con recomendaciones y el detalle de cada plato. En los dos casos el pedido marcha igual: cada ítem cae en su estación, cocina o barra, y la mesa avisa cuando está para servir.",
  },
  {
    id: "charge",
    title: "El cobro cierra el círculo",
    description:
      "Cobrás por cualquier medio y dividís por ítem si hace falta. La factura ARCA la podés emitir en el mismo paso o dejarla para después. El stock baja según la receta y la caja queda lista para el arqueo del cierre.",
  },
  {
    id: "copilot",
    title: "El Copiloto responde y hace",
    description:
      "Cada dato que junta la operación se vuelve una respuesta: “¿cuánto vendí este mes?”, “¿qué plato se vendió más?”. Te contesta, te muestra de dónde sale la información y te sugiere qué hacer con ella. Y si querés, el cambio lo hace él.",
  },
  {
    id: "advisor",
    title: "El Asesor te dice dónde está la plata",
    description:
      "Lee esos mismos números —margen neto, food cost, prime cost, punto de equilibrio— y los convierte en una lista corta: qué tocar hoy, qué mirar esta semana y qué se viene. Con los datos a la vista, para que la decisión la tomes vos.",
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
