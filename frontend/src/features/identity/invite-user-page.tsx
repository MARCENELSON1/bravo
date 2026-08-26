import { useMemo, useState } from "react"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTranslation } from "react-i18next"
import { Link } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { apiErrorText } from "@/api/translate-error"
import { INVITABLE_ROLES } from "@/api/types"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useInviteUser } from "@/hooks/use-invite-user"
import { ROLE_LABELS } from "@/lib/role-labels"

type InviteValues = {
  email: string
  role: "MANAGER" | "WAITER" | "KITCHEN" | "CASHIER"
}

// Route standalone: /app/invite. El contenido vive en <InviteUserForm/> para poder
// reutilizarlo también dentro de la sección "Equipo" de Configuración.
export function InviteUserPage() {
  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-4 px-6 py-10">
      <InviteUserForm showBack />
    </div>
  )
}

export function InviteUserForm({
  showBack = false,
  embedded = false,
}: {
  showBack?: boolean
  embedded?: boolean
}) {
  const { t } = useTranslation()
  const invite = useInviteUser()
  const [serverError, setServerError] = useState<string | null>(null)

  const schema = useMemo(
    () =>
      z.object({
        email: z.email(t("identity.invite.errors.emailInvalid")),
        role: z.enum(["MANAGER", "WAITER", "KITCHEN", "CASHIER"]),
      }),
    [t]
  )

  const {
    register,
    handleSubmit,
    control,
    reset,
    setError,
    formState: { errors },
  } = useForm<InviteValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", role: "WAITER" },
  })

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    invite.mutate(values, {
      onSuccess: () => {
        toast.success(t("identity.invite.sent"))
        reset()
      },
      onError: (error) => {
        if (!isApiError(error)) {
          setServerError(t("identity.invite.genericError"))
          return
        }
        if (error.code === "email_already_registered" || error.code === "invalid_email") {
          setError("email", { message: apiErrorText(error, t, error.message) })
        } else {
          setServerError(apiErrorText(error, t, error.message))
        }
      },
    })
  })

  const emailField = (
    <Field>
      <FieldLabel htmlFor="email">{t("identity.invite.emailLabel")}</FieldLabel>
      <Input id="email" type="email" aria-invalid={!!errors.email} {...register("email")} />
      <FieldError>{errors.email?.message}</FieldError>
    </Field>
  )

  const rolField = (
    <Field>
      <FieldLabel htmlFor="role">{t("identity.invite.roleLabel")}</FieldLabel>
      <Controller
        control={control}
        name="role"
        render={({ field }) => (
          <Select value={field.value} onValueChange={field.onChange}>
            <SelectTrigger id="role" className="w-full">
              <SelectValue placeholder={t("identity.invite.rolePlaceholder")} />
            </SelectTrigger>
            <SelectContent>
              {INVITABLE_ROLES.map((role) => (
                <SelectItem key={role} value={role}>
                  {ROLE_LABELS[role]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      />
      <FieldError>{errors.role?.message}</FieldError>
    </Field>
  )

  // Formulario apilado (página standalone dentro del Card).
  const form = (
    <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
      <FieldGroup>
        {emailField}
        {rolField}
      </FieldGroup>

      <FormError message={serverError} />

      <div className="flex items-center justify-between gap-3">
        {showBack ? (
          <Link to="/app" className="text-sm text-muted-foreground underline underline-offset-4">
            {t("identity.invite.back")}
          </Link>
        ) : (
          <span />
        )}
        <Button type="submit" disabled={invite.isPending}>
          {invite.isPending ? t("identity.invite.submitting") : t("identity.invite.submit")}
        </Button>
      </div>
    </form>
  )

  // Modo embebido: dentro de un GlassCard de Configuración, con la misma estética
  // que el resto de las secciones — a todo el ancho, Rol y Email en dos columnas y
  // el botón abajo a la derecha.
  if (embedded) {
    return (
      <form onSubmit={onSubmit} className="py-5" noValidate>
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground">{t("identity.invite.title")}</p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {t("identity.invite.subtitle")}
            </p>
          </div>
          <Button type="submit" disabled={invite.isPending} className="mt-3 mr-2 shrink-0">
            {invite.isPending ? t("identity.invite.submitting") : t("identity.invite.submit")}
          </Button>
        </div>
        <div className="flex flex-col gap-5">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            {rolField}
            {emailField}
          </div>
          <FormError message={serverError} />
        </div>
      </form>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("identity.invite.title")}</CardTitle>
        <CardDescription>{t("identity.invite.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent>{form}</CardContent>
    </Card>
  )
}
