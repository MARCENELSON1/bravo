// Namespace `products` (P3 gestión): catálogo, menu engineering, precios vs
// inflación, recetas madre y ficha del producto.
export const products = {
  title: "Productos",
  subtitle: "Tu catálogo y precios.",
  newProduct: "Nuevo producto",
  newProductDescription: "El precio se ingresa en la moneda del comercio.",
  created: "Producto creado.",
  createError: "No pudimos crear el producto.",

  // Etiqueta compartida para un componente que es una preparación (receta madre).
  preparationLabel: "Preparación: {{name}}",

  // Acciones cortas reutilizadas en varias tarjetas.
  actions: {
    saving: "Guardando…",
    remove: "Quitar",
    edit: "Editar",
    delete: "Eliminar",
    close: "Cerrar",
    adjust: "Ajustar",
    apply: "Aplicar",
  },

  // Badges de estado compartidos (catálogo, menu engineering, ficha).
  badges: {
    incompleteRecipe: "receta incompleta",
    estimated: "estimado",
  },

  // Alta de producto (Sheet en products-page).
  form: {
    name: "Nombre",
    price: "Precio",
    category: "Categoría (opcional)",
    station: "Estación",
    stationPlaceholder: "Elegí estación…",
    stationKitchen: "Cocina",
    stationBar: "Barra",
    creating: "Creando…",
    create: "Crear producto",
  },
  validation: {
    nameMin: "Mínimo 2 caracteres",
    nameInvalid: "Ingresá un nombre válido",
    priceRequired: "Ingresá un precio",
    pricePositive: "El precio debe ser mayor a 0",
    stationRequired: "Elegí la estación",
  },

  // Catálogo (product-catalog.tsx).
  catalog: {
    title: "Catálogo",
    searchPlaceholder: "Buscar…",
    allCategories: "Todas las categorías",
    statusAll: "Todos",
    statusActive: "Activos",
    statusInactive: "Inactivos",
    columns: {
      name: "Nombre",
      category: "Categoría",
      station: "Estación",
      price: "Precio",
      cost: "Costo",
      leaves: "Te deja",
      sold: "Vendidos",
      status: "Estado",
      recipe: "Receta",
    },
    stationKitchen: "Cocina",
    stationBar: "Barra",
    active: "Activo",
    inactive: "Inactivo",
    incompleteRecipeTitle:
      "El food cost cae fuera de 5–95%: la receta parece incompleta o mal cargada. Revisala.",
    estimatedTitle: "{{pct}}% del costo confirmado con compras",
    noMatch: "Ningún producto coincide con el filtro.",
    empty: "Todavía no cargaste productos.",
    footnote: {
      price: "Precio",
      afterPrice: " en bruto (lo que cobrás); ",
      leaves: "Te deja",
      afterLeaves: " es el margen ",
      netVat: "neto de IVA",
      afterNetVat:
        " y el % es el food cost sobre ese neto. Cargá tu IVA en el Asesor para que el cálculo sea exacto (con IVA sin cargar, neto = bruto).",
    },
  },

  // Editor de receta (RecipeSheet en product-catalog.tsx).
  recipe: {
    button: "Receta",
    sheetTitle: "Receta de {{name}}",
    sheetDescription: "Opcional. Lo que se descuenta de stock por cada unidad vendida.",
    noIngredients: "Cargá insumos en Stock antes de armar la receta.",
    save: "Guardar receta",
    saved: "Receta guardada.",
    saveError: "No pudimos guardar la receta.",
  },

  // Modificadores (Carta QR F2): opciones que el comensal elige por plato.
  modifiers: {
    button: "Opciones",
    sheetTitle: "Opciones de {{name}}",
    sheetDescription:
      "Opcional. Lo que el comensal elige del plato (ej. punto de cocción, agregados).",
    empty: "Sin opciones todavía. Agregá un grupo.",
    addGroup: "Agregar grupo",
    groupNamePlaceholder: "Nombre del grupo (ej. Punto de cocción)",
    min: "Mín.",
    max: "Máx.",
    requiredHint: "Con mín. 1 el grupo es obligatorio.",
    options: "Opciones",
    addOption: "Agregar opción",
    optionNamePlaceholder: "Opción (ej. Con panceta)",
    optionPricePlaceholder: "Extra",
    removeGroup: "Quitar grupo",
    removeOption: "Quitar opción",
    save: "Guardar opciones",
    saving: "Guardando…",
    saved: "Opciones guardadas.",
    saveError: "No pudimos guardar. Revisá los grupos y opciones.",
  },

  // Ficha del producto (product-ficha.tsx).
  ficha: {
    button: "Ficha",
    sheetTitle: "Ficha de {{name}}",
    sheetDescription: "Costo, receta, evolución del costo e insumos del plato.",
    sparklineAria: "Evolución del costo del plato",
    changeStale: "compra hace {{days}}d",
    noPurchases: "sin compras",
    metricPrice: "Precio",
    metricCost: "Costo (bruto)",
    metricLeaves: "Te deja (neto de IVA)",
    metricFoodCost: "Food cost %",
    costConfirmed: "Costo confirmado",
    costEstimated: "Costo estimado",
    coverageHint:
      "{{pct}}% del costo respaldado por compras — cargá las compras que faltan para confirmarlo.",
    ratioHint:
      "El food cost cae fuera de 5–95% ({{pct}}). Revisá la receta antes de confiar en el margen.",
    recipeHeading: "Receta",
    noRecipe: "Este producto no tiene receta.",
    recipeVersion: "Versión de receta: v{{version}}",
    costOverTime: "Costo del plato en el tiempo",
    notEnoughSales:
      "Sin suficientes ventas en el período para graficar. El costo se congela por venta al cobrar.",
    ingredients: "Insumos",
    noDirectIngredients: "Sin insumos directos.",
    ingredientsLegend:
      "▲ = subió desde la primera compra cargada. \"compra hace Nd\" = costo de reposición desactualizado (última compra hace más de 60 días).",
  },

  // Menu engineering (menu-engineering-view.tsx).
  menu: {
    analyzing: "Analizando tu carta…",
    noSales: "Todavía no hay ventas de productos en el período elegido para analizar la carta.",
    heroTitle: "Tu carta",
    heroSummary:
      "De tus {{total}} platos, {{funciona}} son estrellas, {{oportunidad}} son oportunidades, {{revisar}} te están costando margen y {{noVendido}} no se vendieron. Comparados dentro de su categoría de carta.",
    unclassified:
      "{{count}} platos quedaron sin clasificar (pocas ventas en el período o costo sin confirmar) — no los forzamos a una categoría.",
    leftYou: "En este período tu carta te dejó",
    confirmedCount:
      "{{confirmed}} de {{total}} platos con costo confirmado. Los de costo estimado no suman a la plata de arriba — cargá sus compras para confirmarlos.",
    gateClosedPrefix: "Todavía no podemos decirte cuánto te dejó tu carta — te faltan",
    gateClosedSuffix: "platos con costo confirmado (vas {{confirmed}} de {{total}}).",
    loadPurchases: "Cargar compras →",
    cardLeaves: "Te dejan {{amount}}",
    units_one: "{{count}} uds",
    units_other: "{{count}} uds",
    topTitle: "Los 3 platos que más plata te dejan",
    detail: {
      title: "Detalle de productos",
      product: "Producto",
      price: "Precio",
      cost: "Costo",
      leaves: "Te deja",
      sold: "Vendidos",
      status: "Estado",
    },
  },

  // Etiquetas de las 6 categorías de menu engineering. La CLAVE es el enum.
  menuCategories: {
    funciona: { label: "Funciona", sub: "Tu motor — mantenelos" },
    oportunidad: { label: "Oportunidades", sub: "Empujá estos" },
    estable: { label: "Estables", sub: "Tu base — no los toques" },
    revisar: { label: "Revisar", sub: "Están mal, decidí" },
    no_vendido: { label: "No vendidos", sub: "Nadie los pidió" },
    sin_datos: { label: "Sin datos", sub: "Pocas ventas o costo sin confirmar" },
  },

  // Precios vs inflación (pricing-inflation-card.tsx).
  pricing: {
    computeError: "No pudimos calcular los precios vs inflación.",
    title: "Precios vs inflación",
    unconfiguredPre: "Cargá tu ",
    unconfiguredBold: "inflación mensual estimada",
    unconfiguredPost:
      " en el Asesor (Finanzas → Configurar costos) para ver a cuánto debería estar cada precio y qué platos quedaron atrás.",
    inflationLine:
      "Inflación mensual estimada: {{pct}} · las sugerencias se ajustan solas con los días desde el último cambio.",
    allCurrent: "Todo al día",
    laggingBadge_one: "{{count}} precio quedó atrás",
    laggingBadge_other: "{{count}} precios quedaron atrás",
    noneLagging: "Ningún precio quedó rezagado más de un 5% frente a la inflación. 🎉",
    worstPre: "El más rezagado es ",
    worstMid: ": está en {{price}} y debería estar cerca de ",
    worstSuffix: " ({{gap}} por debajo).",
    daysSinceChange_one: "Sin cambios hace {{count}} día",
    daysSinceChange_other: "Sin cambios hace {{count}} días",
    invalidPrice: "Ingresá un precio válido.",
    priceUpdated: "Precio actualizado.",
    updateError: "No pudimos actualizar el precio.",
    newPriceLabel: "Nuevo precio ({{currency}})",
    priceHistory: "Histórico real de precios",
    initialPrice: "Precio inicial: ",
    noChanges: "Sin cambios registrados todavía.",
  },

  // Rotación por día de semana (rotation-schedule.tsx).
  rotation: {
    error: "No pudimos calcular la rotación.",
    title: "Rotación por día",
    subtitle: "Cuánto vendés cada día de la semana y el plato estrella de cada uno.",
    noSales: "Todavía no hay ventas para mostrar la rotación.",
  },
  // Índice 0 = Lunes (coincide con el `weekday` que llega del backend).
  weekdays: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],

  // Recetas madre / preparaciones (preparations-manager.tsx).
  preparations: {
    heading: "Recetas madre",
    subtitle:
      "Preparaciones base reutilizables (ej. salsa fileto). Se usan dentro de las recetas y su costo se propaga solo.",
    new: "Nueva preparación",
    newTitle: "Nueva preparación",
    editTitle: "Editar {{name}}",
    sheetDescription:
      "Una preparación base (receta madre) se usa dentro de varios platos; su costo se prorratea por lo que rinde.",
    empty: "Todavía no cargaste preparaciones.",
    deleteConfirm: "¿Eliminar la preparación \"{{name}}\"?",
    deleted: "Preparación eliminada.",
    deleteError: "No pudimos eliminar la preparación.",
    saved: "Preparación guardada.",
    saveError: "No pudimos guardar la preparación.",
    incomplete: "Cargá nombre, rendimiento y al menos un componente.",
    noIngredients: "Cargá insumos en Stock antes de armar una preparación.",
    nameLabel: "Nombre",
    namePlaceholder: "Salsa fileto",
    yieldLabel: "Rendimiento (cuánto rinde una tanda, en su unidad)",
    yieldPlaceholder: "Ej. 2 (= 2 kg / 2 L / 2 u)",
    componentsLabel: "Componentes",
    save: "Guardar preparación",
    yields: "Rinde {{qty}}",
    componentCount_one: "{{count}} componente",
    componentCount_other: "{{count}} componentes",
    unused: "sin usar",
    usedIn_one: "usada en {{count}} plato",
    usedIn_other: "usada en {{count}} platos",
  },

  // Editor de componentes reutilizable (ComponentRowsEditor).
  components: {
    empty: "Sin componentes. Agregá insumos o preparaciones.",
    selectPlaceholder: "Insumo o preparación",
    qtyPlaceholder: "cant.",
    add: "Agregar componente",
  },
} as const
