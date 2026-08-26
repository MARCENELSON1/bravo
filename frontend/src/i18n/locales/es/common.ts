// Namespace `common`: strings transversales (selector de idioma, etc.).
export const common = {
  language: "Idioma",
  spanish: "Español",
  english: "English",
  // Etiquetas de rol (el código/valor sigue en inglés: OWNER, MANAGER, …).
  roles: {
    OWNER: "Dueño",
    MANAGER: "Encargado",
    WAITER: "Mozo",
    KITCHEN: "Cocina",
    BAR: "Barra",
    CASHIER: "Cajero",
  },
} as const
