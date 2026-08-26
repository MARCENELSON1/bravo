// Namespace `billing` (P3 management). Subscription screen (plans/status/payment).
export const billing = {
  title: "Subscription",
  back: "Back",
  activePlan: "Active plan",
  statusLine: "Status: {{value}}",
  renewsOn: " · renews on {{date}}",
  cancelSubscription: "Cancel subscription",
  canceling: "Canceling…",
  cancelConfirm: "Are you sure you want to cancel your subscription?",
  cancelSuccess: "Subscription canceled.",
  cancelError: "We couldn't cancel it.",
  chooseIntro:
    "Choose a plan to activate your subscription. Payment is secure and processed through {{gateway}}.",
  noPlans: "There are no plans available for your region yet.",
  subscribe: "Subscribe",
  redirecting: "Redirecting…",
  checkoutError: "We couldn't start the payment.",
  interval: {
    month: "month",
    year: "year",
  },
  statusLabels: {
    TRIALING: "Trialing",
    ACTIVE: "Active",
    PAST_DUE: "Past due",
    INCOMPLETE: "Incomplete",
    CANCELED: "Canceled",
  },
} as const
