// Namespace `identity`: alta de comercio, verificación de email e invitaciones
// (onboarding / verify-email / accept-invitation / invite-user).
export const identity = {
  goToLogin: "Ir a iniciar sesión",

  onboarding: {
    title: "Crear comercio",
    description: "Creá tu local y tu cuenta de dueño.",
    footerPrompt: "¿Ya tenés cuenta?",
    footerLink: "Iniciar sesión",
    tenantNameLabel: "Nombre del comercio",
    tenantNamePlaceholder: "Bar La Esquina",
    tenantSlugLabel: "Identificador (slug)",
    tenantSlugPlaceholder: "bar-la-esquina",
    tenantSlugDescription: "Lo usás para iniciar sesión. Solo minúsculas, números y guiones.",
    ownerNameLabel: "Tu nombre",
    ownerNamePlaceholder: "Juan Pérez",
    ownerEmailLabel: "Tu email",
    ownerEmailPlaceholder: "tu@email.com",
    ownerPasswordLabel: "Contraseña",
    ownerPasswordPlaceholder: "********",
    submit: "Crear comercio",
    submitting: "Creando…",
    genericError: "No pudimos crear el comercio.",
    done: {
      title: "Revisá tu email",
      description: "Te enviamos un enlace para verificar tu cuenta.",
      body: "Creamos tu comercio. Para poder ingresar, abrí el email que te mandamos y seguí el enlace de verificación.",
    },
    errors: {
      min2: "Mínimo 2 caracteres",
      maxName: "Máximo 120 caracteres",
      maxSlug: "Máximo 63 caracteres",
      slugFormat: "Solo minúsculas, números y guiones",
      emailInvalid: "Email inválido",
      passwordMin: "Mínimo 8 caracteres",
      passwordMax: "Máximo 128 caracteres",
      ownerNameMax: "Máximo 120 caracteres",
    },
  },

  verifyEmail: {
    verifying: "Verificando tu email",
    loadingHint: "Un momento…",
    invalid: {
      title: "Enlace inválido",
      body: "El enlace de verificación no es válido. Pedí uno nuevo desde tu email.",
    },
    error: {
      title: "No pudimos verificar",
      fallback: "No pudimos verificar tu email.",
    },
    success: {
      title: "Email verificado",
      body: "Tu email quedó verificado. Ya podés iniciar sesión.",
    },
  },

  acceptInvitation: {
    title: "Aceptar invitación",
    description: "Elegí una contraseña para tu cuenta.",
    passwordLabel: "Contraseña",
    submit: "Aceptar invitación",
    submitting: "Aceptando…",
    genericError: "No pudimos aceptar la invitación.",
    invalid: {
      title: "Invitación inválida",
      body: "El enlace de invitación no es válido o expiró. Pedile a tu encargado que te invite de nuevo.",
    },
    done: {
      title: "Invitación aceptada",
      body: "Listo, ya podés iniciar sesión con tu email y la contraseña que elegiste.",
    },
    errors: {
      passwordMin: "Mínimo 8 caracteres",
      passwordMax: "Máximo 128 caracteres",
    },
  },

  invite: {
    title: "Invitar a tu equipo",
    subtitle: "Le enviamos un email para que cree su cuenta.",
    emailLabel: "Email",
    roleLabel: "Rol",
    rolePlaceholder: "Elegí un rol",
    back: "Volver",
    submit: "Enviar invitación",
    submitting: "Enviando…",
    sent: "Invitación enviada.",
    genericError: "No pudimos enviar la invitación.",
    errors: {
      emailInvalid: "Email inválido",
    },
  },
} as const
