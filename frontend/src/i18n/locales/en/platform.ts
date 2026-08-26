// Namespace `platform` (P3 management): super-admin plans panel.
export const platform = {
  heading: "Platform · Plans",
  back: "Back",
  newPlan: "New plan",
  catalog: "Catalog",
  empty: "No plans yet. Create the first one with “New plan”.",
  deleted: "Plan deleted.",
  deleteError: "We couldn't delete the plan.",
  // Ciclo de facturación (código = enum, no cambia).
  intervalOptions: {
    MONTH: "Monthly",
    YEAR: "Yearly",
  },
  // Región del plan (código = enum, no cambia).
  regionOptions: {
    AR: "Argentina (ARS)",
    INTL: "International (USD)",
  },
  table: {
    tier: "Plan",
    region: "Region",
    price: "Price",
    interval: "Cycle",
    features: "Features",
    active: "Active",
    edit: "Edit",
    remove: "Delete",
  },
  form: {
    editPlan: "Edit plan",
    tier: "Plan",
    region: "Region",
    price: "Price ({{currency}})",
    interval: "Cycle",
    includes: "Includes",
    active: "Active (visible in pricing)",
    saving: "Saving…",
    saveChanges: "Save changes",
    createPlan: "Create plan",
    cancel: "Cancel",
    invalidPrice: "Enter a valid price.",
    updated: "Plan updated.",
    created: "Plan created.",
    saveError: "We couldn't save the plan.",
  },
} as const
