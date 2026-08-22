import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useForgotPassword } from "@/hooks/use-forgot-password"

const schema = z.object({
  slug: z
    .string()
    .min(2, "Ingresá el comercio")
    .regex(/^[a-z0-9-]+$/, "Solo minúsculas, números y guiones"),
  email: z.email("Email inválido"),
})

type ForgotValues = z.infer<typeof schema>

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
  const forgot = useForgotPassword()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [remembered] = useState(readRemembered)

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
      Volver a iniciar sesión
    </Link>
  )

  if (done) {
    return (
      <AuthLayout title="Revisá tu correo" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          Si hay una cuenta con ese email en ese comercio, te enviamos un correo con las
          instrucciones para restablecer tu contraseña. Revisá también la carpeta de spam.
        </p>
      </AuthLayout>
    )
  }

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    forgot.mutate(values, {
      onSuccess: () => setDone(true),
      onError: (error) =>
        setServerError(
          isApiError(error) ? error.message : "No pudimos enviar el correo. Probá de nuevo."
        ),
    })
  })

  return (
    <AuthLayout
      title="Recuperar contraseña"
      description="Ingresá el comercio y tu email; te enviamos un enlace para restablecerla."
      footer={loginLink}
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="slug">Comercio</FieldLabel>
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
        </FieldGroup>

        <FormError message={serverError} />

        <Button type="submit" className="w-full" disabled={forgot.isPending}>
          {forgot.isPending ? "Enviando…" : "Enviar enlace"}
        </Button>
      </form>
    </AuthLayout>
  )
}
