import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link, useSearchParams } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useAcceptInvitation } from "@/hooks/use-accept-invitation"

const schema = z.object({
  password: z.string().min(8, "Mínimo 8 caracteres").max(128, "Máximo 128 caracteres"),
})

type AcceptValues = z.infer<typeof schema>

export function AcceptInvitationPage() {
  const [params] = useSearchParams()
  const token = params.get("token")
  const accept = useAcceptInvitation()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

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
      Ir a iniciar sesión
    </Link>
  )

  if (!token) {
    return (
      <AuthLayout title="Invitación inválida" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          El enlace de invitación no es válido o expiró. Pedile a tu encargado que te invite de nuevo.
        </p>
      </AuthLayout>
    )
  }

  if (done) {
    return (
      <AuthLayout title="Invitación aceptada" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          Listo, ya podés iniciar sesión con tu email y la contraseña que elegiste.
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
            isApiError(error) ? error.message : "No pudimos aceptar la invitación."
          ),
      }
    )
  })

  return (
    <AuthLayout title="Aceptar invitación" description="Elegí una contraseña para tu cuenta.">
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="password">Contraseña</FieldLabel>
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
          {accept.isPending ? "Aceptando…" : "Aceptar invitación"}
        </Button>
      </form>
    </AuthLayout>
  )
}
