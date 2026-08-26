// Namespace `platform` (P3 gestión): panel super-admin de planes.
export const platform = {
  heading: "Plataforma · Planes",
  back: "Volver",
  newPlan: "Nuevo plan",
  catalog: "Catálogo",
  empty: "Todavía no hay planes. Creá el primero con “Nuevo plan”.",
  deleted: "Plan borrado.",
  deleteError: "No pudimos borrar el plan.",
  // Ciclo de facturación (código = enum, no cambia).
  intervalOptions: {
    MONTH: "Mensual",
    YEAR: "Anual",
  },
  // Región del plan (código = enum, no cambia).
  regionOptions: {
    AR: "Argentina (ARS)",
    INTL: "Internacional (USD)",
  },
  table: {
    tier: "Plan",
    region: "Región",
    price: "Precio",
    interval: "Ciclo",
    features: "Features",
    active: "Activo",
    edit: "Editar",
    remove: "Borrar",
  },
  form: {
    editPlan: "Editar plan",
    tier: "Plan",
    region: "Región",
    price: "Precio ({{currency}})",
    interval: "Ciclo",
    includes: "Incluye",
    active: "Activo (visible en el pricing)",
    saving: "Guardando…",
    saveChanges: "Guardar cambios",
    createPlan: "Crear plan",
    cancel: "Cancelar",
    invalidPrice: "Ingresá un precio válido.",
    updated: "Plan actualizado.",
    created: "Plan creado.",
    saveError: "No pudimos guardar el plan.",
  },
} as const
