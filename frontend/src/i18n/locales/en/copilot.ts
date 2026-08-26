// Namespace `copilot` (P3 management): AI Insights / copilot chat.
export const copilot = {
  title: "Copilot",
  subtitle: "Ask about your business. I'll show you the answer and where it comes from.",
  inputPlaceholder: "How much did I sell this weekend?",
  thinking: "Thinking…",
  ask: "Ask",
  // Question suggestions.
  examples: [
    "How much did I sell this month?",
    "What are my 5 best-selling products?",
    "Which server billed the most?",
    "How many reservations do I have for tomorrow?",
  ],
  disabled: "The copilot isn't enabled on this account yet.",
  errorFallback: "We couldn't answer that question.",
  showSource: "View query and data",
  hideSource: "Hide query and data",
  noRows: "No rows.",
} as const
