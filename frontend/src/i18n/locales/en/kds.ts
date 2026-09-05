// Namespace `kds`: kitchen and bar screens (kds-page, bar-page, station-board).
export const kds = {
  kitchen: {
    title: "Kitchen (KDS)",
    subtitle: "Kitchen items in preparation, live.",
  },
  bar: {
    title: "Bar",
    subtitle: "Bar items (coffee, drinks) in preparation, live.",
  },
  tableLabel: "Table {{number}}",
  // Service courses: the kitchen bumps the whole course, not dish by dish.
  onHold: "On hold",
  courses: {
    IMMEDIATE: "Drinks",
    STARTER: "Starter",
    MAIN: "Main",
    DESSERT: "Dessert",
  },
  delayed: "delayed",
  startPreparing: "Start preparing",
  markReady: "Mark ready",
  empty: "No items in {{station}}.",
  errors: {
    itemUpdateFailed: "The item could not be updated.",
    courseUpdateFailed: "Couldn't update the course.",
  },
} as const
