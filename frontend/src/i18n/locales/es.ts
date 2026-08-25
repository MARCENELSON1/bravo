// Español (rioplatense) — idioma base del producto. Es el default: nadie ve un
// cambio salvo que elija English. Las nuevas pantallas se migran a `t()` de a poco.
export const es = {
  common: {
    language: "Idioma",
    spanish: "Español",
    english: "English",
  },
  login: {
    title: "Iniciar sesión",
    description: "Ingresá con el comercio y tu cuenta.",
    noAccount: "¿No tenés cuenta?",
    createBusiness: "Crear comercio",
    business: "Comercio",
    email: "Email",
    password: "Contraseña",
    remember: "Recordar mi información de inicio de sesión",
    needsVerification:
      "Tenés que verificar tu email antes de ingresar. Revisá tu casilla y seguí el enlace que te enviamos.",
    submit: "Ingresar",
    submitting: "Ingresando…",
    genericError: "No pudimos iniciar sesión.",
    errors: {
      slugRequired: "Ingresá el comercio",
      slugFormat: "Solo minúsculas, números y guiones",
      emailInvalid: "Email inválido",
      passwordRequired: "Ingresá tu contraseña",
    },
  },
} as const
