// English (US) — para vender a restaurantes de EE.UU. Mismas claves que `es`.
export const en = {
  common: {
    language: "Language",
    spanish: "Español",
    english: "English",
  },
  login: {
    title: "Sign in",
    description: "Enter your business and your account.",
    noAccount: "Don't have an account?",
    createBusiness: "Create business",
    business: "Business",
    email: "Email",
    password: "Password",
    remember: "Remember my sign-in details",
    needsVerification:
      "You need to verify your email before signing in. Check your inbox and follow the link we sent you.",
    submit: "Sign in",
    submitting: "Signing in…",
    genericError: "We couldn't sign you in.",
    errors: {
      slugRequired: "Enter the business",
      slugFormat: "Only lowercase letters, numbers and hyphens",
      emailInvalid: "Invalid email",
      passwordRequired: "Enter your password",
    },
  },
} as const
