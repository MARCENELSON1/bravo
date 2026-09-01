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
  cart: {
    increase: "Add one",
    decrease: "Remove one",
    send: "Send order",
    sending: "Sending…",
    total: "Total",
  },
  sent: {
    title: "Order sent!",
    gated: "Your server will confirm it in a moment and send it to the kitchen.",
    kitchen: "It's in the kitchen 🍳",
    again: "Order more",
  },
  toast: {
    waiterOnTheWay: "Your server is on the way 🙌",
    billOnTheWay: "Your check is on the way 🙌",
    failed: "We couldn't notify. Please try again.",
    orderFailed: "We couldn't send your order. Please try again.",
    orderUnavailable: "One of the dishes is no longer available. Please review your order.",
  },
  poweredBy: "with Wellnod",
} as const
