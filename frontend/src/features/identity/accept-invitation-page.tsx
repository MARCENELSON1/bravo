import { useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTranslation } from "react-i18next"
import { Link, useSearchParams } from "react-router-dom"

import { apiErrorText } from "@/api/translate-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useAcceptInvitation } from "@/hooks/use-accept-invitation"

type AcceptValues = { password: string }

export function AcceptInvitationPage() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const token = params.get("token")
  const accept = useAcceptInvitation()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const schema = useMemo(
    () =>
      z.object({
        password: z
          .string()
          .min(8, t("identity.acceptInvitation.errors.passwordMin"))
          .max(128, t("identity.acceptInvitation.errors.passwordMax")),
      }),
    [t]
  )

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AcceptValues>({
    resolver: zodResolver(schema),
    defaultValues: { password: "" },
  })

  const loginLink = (
    <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
      {t("identity.goToLogin")}
    </Link>
  )

  if (!token) {
    return (
      <AuthLayout title={t("identity.acceptInvitation.invalid.title")} footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          {t("identity.acceptInvitation.invalid.body")}
        </p>
      </AuthLayout>
    )
  }

  if (done) {
    return (
      <AuthLayout title={t("identity.acceptInvitation.done.title")} footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          {t("identity.acceptInvitation.done.body")}
        </p>
      </AuthLayout>
    )
  }

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    accept.mutate(
      { token, password: values.password },
      {
        onSuccess: () => setDone(true),
        onError: (error) =>
          setServerError(
            apiErrorText(error, t, t("identity.acceptInvitation.genericError"))
          ),
      }
    )
  })

  return (
    <AuthLayout title={t("identity.acceptInvitation.title")} description={t("identity.acceptInvitation.description")}>
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="password">{t("identity.acceptInvitation.passwordLabel")}</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              aria-invalid={!!errors.password}
              {...register("password")}
            />
            <FieldError>{errors.password?.message}</FieldError>
          </Field>
        </FieldGroup>

        <FormError message={serverError} />

        <Button type="submit" className="w-full" disabled={accept.isPending}>
          {accept.isPending ? t("identity.acceptInvitation.submitting") : t("identity.acceptInvitation.submit")}
        </Button>
      </form>
    </AuthLayout>
  )
}
