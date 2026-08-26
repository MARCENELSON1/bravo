// Namespace `login`: pantalla de inicio de sesión (ya migrada, es la referencia).
export const login = {
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
} as const
