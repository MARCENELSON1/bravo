import { useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTranslation } from "react-i18next"
import { Link } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import { apiErrorText } from "@/api/translate-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useOnboarding } from "@/hooks/use-onboarding"

type OnboardingValues = {
  tenantName: string
  tenantSlug: string
  ownerEmail: string
  ownerPassword: string
  ownerName?: string
}

export function OnboardingPage() {
  const { t } = useTranslation()
  const onboarding = useOnboarding()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const schema = useMemo(
    () =>
      z.object({
        tenantName: z
          .string()
          .min(2, t("identity.onboarding.errors.min2"))
          .max(120, t("identity.onboarding.errors.maxName")),
        tenantSlug: z
          .string()
          .min(2, t("identity.onboarding.errors.min2"))
          .max(63, t("identity.onboarding.errors.maxSlug"))
          .regex(/^[a-z0-9-]+$/, t("identity.onboarding.errors.slugFormat")),
        ownerEmail: z.email(t("identity.onboarding.errors.emailInvalid")),
        ownerPassword: z
          .string()
          .min(8, t("identity.onboarding.errors.passwordMin"))
          .max(128, t("identity.onboarding.errors.passwordMax")),
        ownerName: z.string().max(120, t("identity.onboarding.errors.ownerNameMax")).optional(),
      }),
    [t]
  )

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<OnboardingValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      tenantName: "",
      tenantSlug: "",
      ownerEmail: "",
      ownerPassword: "",
      ownerName: "",
    },
  })

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    onboarding.mutate(
      {
        tenant_name: values.tenantName,
        tenant_slug: values.tenantSlug,
        owner_email: values.ownerEmail,
        owner_password: values.ownerPassword,
        owner_name: values.ownerName?.trim() ? values.ownerName.trim() : undefined,
      },
      {
        onSuccess: () => setDone(true),
        onError: (error) => {
          if (!isApiError(error)) {
            setServerError(t("identity.onboarding.genericError"))
            return
          }
          if (error.code === "tenant_already_exists") {
            setError("tenantSlug", { message: apiErrorText(error, t, error.message) })
          } else if (error.code === "email_already_registered" || error.code === "invalid_email") {
            setError("ownerEmail", { message: apiErrorText(error, t, error.message) })
          } else {
            setServerError(apiErrorText(error, t, error.message))
          }
        },
      }
    )
  })

  if (done) {
    return (
      <AuthLayout
        title={t("identity.onboarding.done.title")}
        description={t("identity.onboarding.done.description")}
        footer={
          <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
            {t("identity.goToLogin")}
          </Link>
        }
      >
        <p className="text-sm text-muted-foreground">
          {t("identity.onboarding.done.body")}
        </p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title={t("identity.onboarding.title")}
      description={t("identity.onboarding.description")}
      footer={
        <span>
          {t("identity.onboarding.footerPrompt")}{" "}
          <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
            {t("identity.onboarding.footerLink")}
          </Link>
        </span>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="tenantName">{t("identity.onboarding.tenantNameLabel")}</FieldLabel>
            <Input id="tenantName" placeholder={t("identity.onboarding.tenantNamePlaceholder")} aria-invalid={!!errors.tenantName} {...register("tenantName")} />
            <FieldError>{errors.tenantName?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="tenantSlug">{t("identity.onboarding.tenantSlugLabel")}</FieldLabel>
            <Input
              id="tenantSlug"
              placeholder={t("identity.onboarding.tenantSlugPlaceholder")}
              autoCapitalize="none"
              autoCorrect="off"
              aria-invalid={!!errors.tenantSlug}
              {...register("tenantSlug")}
            />
            <FieldDescription>{t("identity.onboarding.tenantSlugDescription")}</FieldDescription>
            <FieldError>{errors.tenantSlug?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="ownerName">{t("identity.onboarding.ownerNameLabel")}</FieldLabel>
            <Input
              id="ownerName"
              placeholder={t("identity.onboarding.ownerNamePlaceholder")}
              autoComplete="name"
              aria-invalid={!!errors.ownerName}
              {...register("ownerName")}
            />
            <FieldError>{errors.ownerName?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="ownerEmail">{t("identity.onboarding.ownerEmailLabel")}</FieldLabel>
            <Input id="ownerEmail" type="email" placeholder={t("identity.onboarding.ownerEmailPlaceholder")} autoComplete="email" aria-invalid={!!errors.ownerEmail} {...register("ownerEmail")} />
            <FieldError>{errors.ownerEmail?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="ownerPassword">{t("identity.onboarding.ownerPasswordLabel")}</FieldLabel>
            <Input id="ownerPassword" type="password" placeholder={t("identity.onboarding.ownerPasswordPlaceholder")} autoComplete="new-password" aria-invalid={!!errors.ownerPassword} {...register("ownerPassword")} />
            <FieldError>{errors.ownerPassword?.message}</FieldError>
          </Field>
        </FieldGroup>

        <FormError message={serverError} />

        <Button type="submit" className="w-full" disabled={onboarding.isPending}>
          {onboarding.isPending ? t("identity.onboarding.submitting") : t("identity.onboarding.submit")}
        </Button>
      </form>
    </AuthLayout>
  )
}
