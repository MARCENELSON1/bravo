// Namespace `products` (P3 management): catalog, menu engineering, prices vs
// inflation, base recipes and product sheet.
export const products = {
  title: "Products",
  subtitle: "Your catalog and prices.",
  newProduct: "New product",
  newProductDescription: "The price is entered in the business currency.",
  created: "Product created.",
  createError: "We couldn't create the product.",

  // Etiqueta compartida para un componente que es una preparación (receta madre).
  preparationLabel: "Preparation: {{name}}",

  // Acciones cortas reutilizadas en varias tarjetas.
  actions: {
    saving: "Saving…",
    remove: "Remove",
    edit: "Edit",
    delete: "Delete",
    close: "Close",
    adjust: "Adjust",
    apply: "Apply",
  },

  // Badges de estado compartidos (catálogo, menu engineering, ficha).
  badges: {
    incompleteRecipe: "incomplete recipe",
    estimated: "estimated",
  },

  // Alta de producto (Sheet en products-page).
  form: {
    name: "Name",
    price: "Price",
    category: "Category (optional)",
    station: "Station",
    stationPlaceholder: "Choose a station…",
    stationKitchen: "Kitchen",
    stationBar: "Bar",
    creating: "Creating…",
    create: "Create product",
  },
  validation: {
    nameMin: "At least 2 characters",
    nameInvalid: "Enter a valid name",
    priceRequired: "Enter a price",
    pricePositive: "The price must be greater than 0",
    stationRequired: "Choose the station",
  },

  // Catálogo (product-catalog.tsx).
  catalog: {
    title: "Catalog",
    searchPlaceholder: "Search…",
    allCategories: "All categories",
    statusAll: "All",
    statusActive: "Active",
    statusInactive: "Inactive",
    columns: {
      name: "Name",
      category: "Category",
      station: "Station",
      price: "Price",
      cost: "Cost",
      leaves: "You keep",
      sold: "Sold",
      status: "Status",
      recipe: "Recipe",
    },
    stationKitchen: "Kitchen",
    stationBar: "Bar",
    active: "Active",
    inactive: "Inactive",
    incompleteRecipeTitle:
      "The food cost falls outside 5–95%: the recipe looks incomplete or misconfigured. Review it.",
    estimatedTitle: "{{pct}}% of the cost confirmed with purchases",
    noMatch: "No product matches the filter.",
    empty: "You haven't added any products yet.",
    footnote: {
      price: "Price",
      afterPrice: " is gross (what you charge); ",
      leaves: "You keep",
      afterLeaves: " is the margin ",
      netVat: "net of sales tax",
      afterNetVat:
        " and the % is the food cost over that net. Enter your sales tax in the Advisor so the math is exact (with no tax set, net = gross).",
    },
  },

  // Editor de receta (RecipeSheet en product-catalog.tsx).
  recipe: {
    button: "Recipe",
    sheetTitle: "Recipe for {{name}}",
    sheetDescription: "Optional. What's deducted from stock for each unit sold.",
    noIngredients: "Add ingredients in Supplies before building the recipe.",
    save: "Save recipe",
    saved: "Recipe saved.",
    saveError: "We couldn't save the recipe.",
  },

  // Modifiers (Carta QR F2): choices the diner picks per dish.
  modifiers: {
    button: "Options",
    sheetTitle: "Options for {{name}}",
    sheetDescription:
      "Optional. What the diner picks for the dish (e.g. doneness, add-ons).",
    empty: "No options yet. Add a group.",
    addGroup: "Add group",
    groupNamePlaceholder: "Group name (e.g. Doneness)",
    min: "Min",
    max: "Max",
    requiredHint: "With min 1 the group is required.",
    options: "Options",
    addOption: "Add option",
    optionNamePlaceholder: "Option (e.g. Add bacon)",
    optionPricePlaceholder: "Extra",
    removeGroup: "Remove group",
    removeOption: "Remove option",
    save: "Save options",
    saving: "Saving…",
    saved: "Options saved.",
    saveError: "We couldn't save. Check the groups and options.",
  },

  // Ficha del producto (product-ficha.tsx).
  ficha: {
    button: "Details",
    sheetTitle: "Details for {{name}}",
    sheetDescription: "Cost, recipe, cost trend and the dish's ingredients.",
    sparklineAria: "Dish cost trend",
    changeStale: "bought {{days}}d ago",
    noPurchases: "no purchases",
    metricPrice: "Price",
    metricCost: "Cost (gross)",
    metricLeaves: "You keep (net of sales tax)",
    metricFoodCost: "Food cost %",
    costConfirmed: "Confirmed cost",
    costEstimated: "Estimated cost",
    coverageHint:
      "{{pct}}% of the cost backed by purchases — add the missing purchases to confirm it.",
    ratioHint:
      "The food cost falls outside 5–95% ({{pct}}). Review the recipe before trusting the margin.",
    recipeHeading: "Recipe",
    noRecipe: "This product has no recipe.",
    recipeVersion: "Recipe version: v{{version}}",
    costOverTime: "Dish cost over time",
    notEnoughSales:
      "Not enough sales in the period to chart. The cost is frozen per sale at checkout.",
    ingredients: "Ingredients",
    noDirectIngredients: "No direct ingredients.",
    ingredientsLegend:
      "▲ = up since the first recorded purchase. \"bought Nd ago\" = replacement cost out of date (last purchase over 60 days ago).",
  },

  // Menu engineering (menu-engineering-view.tsx).
  menu: {
    analyzing: "Analyzing your menu…",
    noSales: "No product sales in the selected period yet to analyze the menu.",
    heroTitle: "Your menu",
    heroSummary:
      "Of your {{total}} dishes, {{funciona}} are stars, {{oportunidad}} are opportunities, {{revisar}} are costing you margin and {{noVendido}} didn't sell. Compared within their menu category.",
    unclassified:
      "{{count}} dishes were left unclassified (few sales in the period or unconfirmed cost) — we don't force them into a category.",
    leftYou: "This period your menu made you",
    confirmedCount:
      "{{confirmed}} of {{total}} dishes with confirmed cost. The ones with estimated cost don't add to the money above — add their purchases to confirm them.",
    gateClosedPrefix: "We can't tell you yet how much your menu made — you're missing",
    gateClosedSuffix: "dishes with confirmed cost (you're at {{confirmed}} of {{total}}).",
    loadPurchases: "Add purchases →",
    cardLeaves: "They keep {{amount}}",
    units_one: "{{count}} units",
    units_other: "{{count}} units",
    topTitle: "The 3 dishes that make you the most money",
    detail: {
      title: "Product detail",
      product: "Product",
      price: "Price",
      cost: "Cost",
      leaves: "You keep",
      sold: "Sold",
      status: "Status",
    },
  },

  // Etiquetas de las 6 categorías de menu engineering. La CLAVE es el enum.
  menuCategories: {
    funciona: { label: "Working", sub: "Your engine — keep them" },
    oportunidad: { label: "Opportunities", sub: "Push these" },
    estable: { label: "Stable", sub: "Your base — don't touch them" },
    revisar: { label: "Review", sub: "They're off, decide" },
    no_vendido: { label: "Not sold", sub: "Nobody ordered them" },
    sin_datos: { label: "No data", sub: "Few sales or unconfirmed cost" },
  },

  // Precios vs inflación (pricing-inflation-card.tsx).
  pricing: {
    computeError: "We couldn't calculate prices vs inflation.",
    title: "Prices vs inflation",
    unconfiguredPre: "Enter your ",
    unconfiguredBold: "estimated monthly inflation",
    unconfiguredPost:
      " in the Advisor (Finance → Configure costs) to see what each price should be and which dishes fell behind.",
    inflationLine:
      "Estimated monthly inflation: {{pct}} · suggestions adjust on their own with the days since the last change.",
    allCurrent: "All up to date",
    laggingBadge_one: "{{count}} price fell behind",
    laggingBadge_other: "{{count}} prices fell behind",
    noneLagging: "No price fell more than 5% behind inflation.",
    worstPre: "The one furthest behind is ",
    worstMid: ": it's at {{price}} and should be near ",
    worstSuffix: " ({{gap}} below).",
    daysSinceChange_one: "Unchanged for {{count}} day",
    daysSinceChange_other: "Unchanged for {{count}} days",
    invalidPrice: "Enter a valid price.",
    priceUpdated: "Price updated.",
    updateError: "We couldn't update the price.",
    newPriceLabel: "New price ({{currency}})",
    priceHistory: "Actual price history",
    initialPrice: "Initial price: ",
    noChanges: "No changes recorded yet.",
  },

  // Rotación por día de semana (rotation-schedule.tsx).
  rotation: {
    error: "We couldn't calculate the rotation.",
    title: "Rotation by day",
    subtitle: "How much you sell each day of the week and each day's top dish.",
    noSales: "No sales yet to show the rotation.",
  },
  // Índice 0 = Lunes (coincide con el `weekday` que llega del backend).
  weekdays: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],

  // Recetas madre / preparaciones (preparations-manager.tsx).
  preparations: {
    heading: "Base recipes",
    subtitle:
      "Reusable base preparations (e.g. marinara sauce). They're used inside recipes and their cost propagates automatically.",
    new: "New preparation",
    newTitle: "New preparation",
    editTitle: "Edit {{name}}",
    sheetDescription:
      "A base preparation (mother recipe) is used inside several dishes; its cost is prorated by its yield.",
    empty: "You haven't added any preparations yet.",
    deleteConfirm: "Delete the preparation \"{{name}}\"?",
    deleted: "Preparation deleted.",
    deleteError: "We couldn't delete the preparation.",
    saved: "Preparation saved.",
    saveError: "We couldn't save the preparation.",
    incomplete: "Enter a name, yield and at least one component.",
    noIngredients: "Add ingredients in Supplies before building a preparation.",
    nameLabel: "Name",
    namePlaceholder: "Marinara sauce",
    yieldLabel: "Yield (how much one batch makes, in its unit)",
    yieldPlaceholder: "e.g. 2 (= 2 kg / 2 L / 2 u)",
    componentsLabel: "Components",
    save: "Save preparation",
    yields: "Yields {{qty}}",
    componentCount_one: "{{count}} component",
    componentCount_other: "{{count}} components",
    unused: "unused",
    usedIn_one: "used in {{count}} dish",
    usedIn_other: "used in {{count}} dishes",
  },

  // Editor de componentes reutilizable (ComponentRowsEditor).
  components: {
    empty: "No components. Add ingredients or preparations.",
    selectPlaceholder: "Ingredient or preparation",
    qtyPlaceholder: "qty",
    add: "Add component",
  },
} as const
