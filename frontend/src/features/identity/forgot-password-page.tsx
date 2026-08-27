import { useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTranslation } from "react-i18next"
import { Link } from "react-router-dom"

import { apiErrorText } from "@/api/translate-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useForgotPassword } from "@/hooks/use-forgot-password"

type ForgotValues = { slug: string; email: string }

// Prefill del "Recordarme" del login (comercio + email), si existe.
const REMEMBER_KEY = "wellnod:login-remember"
function readRemembered(): { slug: string; email: string } {
  try {
    const raw = localStorage.getItem(REMEMBER_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (typeof parsed?.slug === "string" && typeof parsed?.email === "string") {
        return { slug: parsed.slug, email: parsed.email }
      }
    }
  } catch {
    // storage corrupto: lo ignoramos
  }
  return { slug: "", email: "" }
}

export function ForgotPasswordPage() {
  const { t } = useTranslation()
  const forgot = useForgotPassword()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [remembered] = useState(readRemembered)

  const schema = useMemo(
    () =>
      z.object({
        slug: z
          .string()
          .min(2, t("identity.forgotPassword.errors.slugRequired"))
          .regex(/^[a-z0-9-]+$/, t("identity.forgotPassword.errors.slugFormat")),
        email: z.email(t("identity.forgotPassword.errors.emailInvalid")),
      }),
    [t]
  )

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotValues>({
    resolver: zodResolver(schema),
    defaultValues: { slug: remembered.slug, email: remembered.email },
  })

  const loginLink = (
    <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
      {t("identity.forgotPassword.backToLogin")}
    </Link>
  )

  if (done) {
    return (
      <AuthLayout title={t("identity.forgotPassword.done.title")} footer={loginLink}>
        <p className="text-sm text-muted-foreground">{t("identity.forgotPassword.done.body")}</p>
      </AuthLayout>
    )
  }

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    forgot.mutate(values, {
      onSuccess: () => setDone(true),
      onError: (error) =>
        setServerError(apiErrorText(error, t, t("identity.forgotPassword.genericError"))),
    })
  })

  return (
    <AuthLayout
      title={t("identity.forgotPassword.title")}
      description={t("identity.forgotPassword.description")}
      footer={loginLink}
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="slug">{t("identity.forgotPassword.businessLabel")}</FieldLabel>
            <Input
              id="slug"
              autoCapitalize="none"
              autoCorrect="off"
              aria-invalid={!!errors.slug}
              {...register("slug")}
            />
            <FieldError>{errors.slug?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="email">{t("identity.forgotPassword.emailLabel")}</FieldLabel>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={!!errors.email}
              {...register("email")}
            />
            <FieldError>{errors.email?.message}</FieldError>
          </Field>
        </FieldGroup>

        <FormError message={serverError} />

        <Button type="submit" className="w-full" disabled={forgot.isPending}>
          {forgot.isPending
            ? t("identity.forgotPassword.submitting")
            : t("identity.forgotPassword.submit")}
        </Button>
      </form>
    </AuthLayout>
  )
}
