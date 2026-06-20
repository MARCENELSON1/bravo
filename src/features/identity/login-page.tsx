import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link, useLocation, useNavigate } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useLogin } from "@/hooks/use-login"

const schema = z.object({
  slug: z
    .string()
    .min(2, "Ingresá el comercio")
    .regex(/^[a-z0-9-]+$/, "Solo minúsculas, números y guiones"),
  email: z.email("Email inválido"),
  password: z.string().min(1, "Ingresá tu contraseña"),
})

type LoginValues = z.infer<typeof schema>

export function LoginPage() {
  const login = useLogin()
  const navigate = useNavigate()
  const location = useLocation()
  const [serverError, setServerError] = useState<string | null>(null)
  const [needsVerification, setNeedsVerification] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({
    resolver: zodResolver(schema),
    defaultValues: { slug: "", email: "", password: "" },
  })

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    setNeedsVerification(false)
    login.mutate(values, {
      onSuccess: () => {
        const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname
        navigate(from ?? "/app", { replace: true })
      },
      onError: (error) => {
        // Product decision: email_not_verified shows a guiding notice, not a
        // neutral error (UX over strict anti-enumeration).
        if (isApiError(error) && error.code === "email_not_verified") {
          setNeedsVerification(true)
          return
        }
        setServerError(isApiError(error) ? error.message : "No pudimos iniciar sesión.")
      },
    })
  })

  return (
    <AuthLayout
      title="Iniciar sesión"
      description="Ingresá con el comercio y tu cuenta."
      footer={
        <span>
          ¿No tenés cuenta?{" "}
          <Link to="/onboarding" className="font-medium text-foreground underline underline-offset-4">
            Crear comercio
          </Link>
        </span>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="slug">Comercio</FieldLabel>
            <Input
              id="slug"
              placeholder="mi-bar"
              autoCapitalize="none"
              autoCorrect="off"
              aria-invalid={!!errors.slug}
              {...register("slug")}
            />
            <FieldError>{errors.slug?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              aria-invalid={!!errors.email}
              {...register("email")}
            />
            <FieldError>{errors.email?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="password">Contraseña</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              aria-invalid={!!errors.password}
              {...register("password")}
            />
            <FieldError>{errors.password?.message}</FieldError>
          </Field>
        </FieldGroup>

        {needsVerification ? (
          <div
            role="alert"
            className="rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm text-foreground"
          >
            Tenés que verificar tu email antes de ingresar. Revisá tu casilla y seguí el
            enlace que te enviamos.
          </div>
        ) : null}

        <FormError message={serverError} />

        <Button type="submit" className="w-full" disabled={login.isPending}>
          {login.isPending ? "Ingresando…" : "Ingresar"}
        </Button>
      </form>
    </AuthLayout>
  )
}
