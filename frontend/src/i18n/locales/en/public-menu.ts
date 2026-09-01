// Customer-facing QR menu (public route /carta/:token). Bilingual UI; the menu
// content (dish names) stays in whatever language the owner entered.
export const publicMenu = {
  loading: "Loading the menu…",
  menu: "Menu",
  uncategorized: "Other",
  soldOut: "Sold out",
  empty: {
    title: "Menu coming soon",
    body: "No dishes yet. Ask your server for the menu.",
  },
  invalid: {
    title: "We couldn't open the menu",
    body: "Ask your server for the QR code, or scan again.",
  },
  error: {
    title: "Something went wrong",
    body: "We couldn't load the menu. Please try again in a moment.",
  },
  actions: {
    callWaiter: "Call the server",
    requestBill: "Ask for the check",
  },
  toast: {
    waiterOnTheWay: "Your server is on the way 🙌",
    billOnTheWay: "Your check is on the way 🙌",
    failed: "We couldn't notify. Please try again.",
  },
  poweredBy: "with Wellnod",
} as const
