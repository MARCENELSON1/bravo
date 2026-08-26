// Namespace `identity`: business signup, email verification and invitations
// (onboarding / verify-email / accept-invitation / invite-user).
export const identity = {
  goToLogin: "Go to sign in",

  onboarding: {
    title: "Create business",
    description: "Set up your location and your owner account.",
    footerPrompt: "Already have an account?",
    footerLink: "Sign in",
    tenantNameLabel: "Business name",
    tenantNamePlaceholder: "The Corner Bar",
    tenantSlugLabel: "Identifier (slug)",
    tenantSlugPlaceholder: "the-corner-bar",
    tenantSlugDescription: "You use it to sign in. Only lowercase letters, numbers and hyphens.",
    ownerNameLabel: "Your name",
    ownerNamePlaceholder: "John Smith",
    ownerEmailLabel: "Your email",
    ownerEmailPlaceholder: "you@email.com",
    ownerPasswordLabel: "Password",
    ownerPasswordPlaceholder: "********",
    submit: "Create business",
    submitting: "Creating…",
    genericError: "We couldn't create the business.",
    done: {
      title: "Check your email",
      description: "We sent you a link to verify your account.",
      body: "We created your business. To sign in, open the email we sent you and follow the verification link.",
    },
    errors: {
      min2: "At least 2 characters",
      maxName: "At most 120 characters",
      maxSlug: "At most 63 characters",
      slugFormat: "Only lowercase letters, numbers and hyphens",
      emailInvalid: "Invalid email",
      passwordMin: "At least 8 characters",
      passwordMax: "At most 128 characters",
      ownerNameMax: "At most 120 characters",
    },
  },

  verifyEmail: {
    verifying: "Verifying your email",
    loadingHint: "One moment…",
    invalid: {
      title: "Invalid link",
      body: "The verification link isn't valid. Request a new one from your email.",
    },
    error: {
      title: "We couldn't verify",
      fallback: "We couldn't verify your email.",
    },
    success: {
      title: "Email verified",
      body: "Your email is verified. You can sign in now.",
    },
  },

  acceptInvitation: {
    title: "Accept invitation",
    description: "Choose a password for your account.",
    passwordLabel: "Password",
    submit: "Accept invitation",
    submitting: "Accepting…",
    genericError: "We couldn't accept the invitation.",
    invalid: {
      title: "Invalid invitation",
      body: "The invitation link isn't valid or has expired. Ask your manager to invite you again.",
    },
    done: {
      title: "Invitation accepted",
      body: "You're all set. You can now sign in with your email and the password you chose.",
    },
    errors: {
      passwordMin: "At least 8 characters",
      passwordMax: "At most 128 characters",
    },
  },

  invite: {
    title: "Invite your team",
    subtitle: "We'll send them an email to create their account.",
    emailLabel: "Email",
    roleLabel: "Role",
    rolePlaceholder: "Choose a role",
    back: "Back",
    submit: "Send invitation",
    submitting: "Sending…",
    sent: "Invitation sent.",
    genericError: "We couldn't send the invitation.",
    errors: {
      emailInvalid: "Invalid email",
    },
  },
} as const
