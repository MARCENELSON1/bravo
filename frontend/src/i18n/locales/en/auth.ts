// Namespace `auth`: the brand column of the identity screens
// (components/auth/auth-layout.tsx).
//
// The title is THE SAME as the landing hero, and the three points are its three
// product groups (The shift / The business / The decisions): whoever arrives from
// the site should recognize the promise they came in with.
export const auth = {
  brandTitleBefore: "Your whole restaurant, ",
  brandTitleHighlight: "in one app",
  brandSubtitle:
    "No scattered apps, no spreadsheets to export. The whole restaurant runs on the same data.",
  bullets: {
    shift: {
      label: "The shift",
      text: "Tables, orders, kitchen, register, and tax, live.",
    },
    business: {
      label: "The business",
      text: "Menu with costs, inventory, reservations, team, and finance.",
    },
    decisions: {
      label: "The decisions",
      text: "The Copilot answers with your data and the Advisor tells you what to do.",
    },
  },
} as const
