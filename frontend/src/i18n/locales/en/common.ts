// Namespace `common`: cross-cutting strings (language switcher, etc.).
export const common = {
  language: "Language",
  spanish: "Español",
  english: "English",
  // Role labels (the code/value stays English: OWNER, MANAGER, …).
  roles: {
    OWNER: "Owner",
    MANAGER: "Manager",
    WAITER: "Server",
    KITCHEN: "Kitchen",
    BAR: "Bar",
    CASHIER: "Cashier",
  },
} as const
