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
import { useResetPassword } from "@/hooks/use-reset-password"

const schema = z.object({
  password: z.string().min(8, "Mínimo 8 caracteres").max(128, "Máximo 128 caracteres"),
})

type ResetValues = z.infer<typeof schema>

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get("token")
  const reset = useResetPassword()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetValues>({
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
      <AuthLayout title="Enlace inválido" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          El enlace para restablecer la contraseña no es válido o expiró. Pedí uno nuevo desde
          "¿Olvidaste tu contraseña?".
        </p>
      </AuthLayout>
    )
  }

  if (done) {
    return (
      <AuthLayout title="Contraseña actualizada" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          Listo, ya podés iniciar sesión con tu nueva contraseña.
        </p>
      </AuthLayout>
    )
  }

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    reset.mutate(
      { token, password: values.password },
      {
        onSuccess: () => setDone(true),
        onError: (error) =>
          setServerError(
            isApiError(error) ? error.message : "No pudimos actualizar la contraseña."
          ),
      }
    )
  })

  return (
    <AuthLayout title="Nueva contraseña" description="Elegí una contraseña nueva para tu cuenta.">
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

        <Button type="submit" className="w-full" disabled={reset.isPending}>
          {reset.isPending ? "Guardando…" : "Guardar contraseña"}
        </Button>
      </form>
    </AuthLayout>
  )
}
