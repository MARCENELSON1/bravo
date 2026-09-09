// Namespace `auth`: the brand column of the identity screens
// (components/auth/auth-shell.tsx).
//
// The title is THE SAME as the landing hero, and the three points are its three
// product groups with the SAME areas inside each one (see the list in
// landing/src/infrastructure/repositories/en-static-content-repository.ts): whoever
// arrives from the site should recognize the promise they came in with, and missing
// areas here would make the product look smaller than what they were shown.
//
// The Copilot is described by what it does today — answer with your data — not by
// what it will do. Promising something that does not exist yet to someone who is
// creating their account gets found out five minutes later.
export const auth = {
  brandTitleBefore: "Your whole restaurant, ",
  brandTitleHighlight: "in one app",
  brandSubtitle:
    "No scattered apps, no spreadsheets to export. The whole restaurant runs on the same data.",
  bullets: {
    shift: {
      label: "The shift",
      text: "Tables, orders, kitchen and bar, register, tax, and reservations: the whole service, live.",
    },
    business: {
      label: "The business",
      text: "Menu with its costs, inventory, guests, team, time tracking, and finance, all in one place.",
    },
    decisions: {
      label: "The decisions",
      text: "Reports up to date, a Copilot that answers with your data, and an Advisor that tells you what to do.",
    },
  },
} as const
