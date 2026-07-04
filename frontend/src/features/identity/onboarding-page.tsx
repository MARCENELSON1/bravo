import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useOnboarding } from "@/hooks/use-onboarding"

const schema = z.object({
  tenantName: z.string().min(2, "Mínimo 2 caracteres").max(120, "Máximo 120 caracteres"),
  tenantSlug: z
    .string()
    .min(2, "Mínimo 2 caracteres")
    .max(63, "Máximo 63 caracteres")
    .regex(/^[a-z0-9-]+$/, "Solo minúsculas, números y guiones"),
  ownerEmail: z.email("Email inválido"),
  ownerPassword: z.string().min(8, "Mínimo 8 caracteres").max(128, "Máximo 128 caracteres"),
  ownerName: z.string().max(120, "Máximo 120 caracteres").optional(),
})

type OnboardingValues = z.infer<typeof schema>

export function OnboardingPage() {
  const onboarding = useOnboarding()
  const [serverError, setServerError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

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
            setServerError("No pudimos crear el comercio.")
            return
          }
          if (error.code === "tenant_already_exists") {
            setError("tenantSlug", { message: error.message })
          } else if (error.code === "email_already_registered" || error.code === "invalid_email") {
            setError("ownerEmail", { message: error.message })
          } else {
            setServerError(error.message)
          }
        },
      }
    )
  })

  if (done) {
    return (
      <AuthLayout
        title="Revisá tu email"
        description="Te enviamos un enlace para verificar tu cuenta."
        footer={
          <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
            Ir a iniciar sesión
          </Link>
        }
      >
        <p className="text-sm text-muted-foreground">
          Creamos tu comercio. Para poder ingresar, abrí el email que te mandamos y seguí el
          enlace de verificación.
        </p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title="Crear comercio"
      description="Creá tu local y tu cuenta de dueño."
      footer={
        <span>
          ¿Ya tenés cuenta?{" "}
          <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
            Iniciar sesión
          </Link>
        </span>
      }
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="tenantName">Nombre del comercio</FieldLabel>
            <Input id="tenantName" placeholder="Bar La Esquina" aria-invalid={!!errors.tenantName} {...register("tenantName")} />
            <FieldError>{errors.tenantName?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="tenantSlug">Identificador (slug)</FieldLabel>
            <Input
              id="tenantSlug"
              placeholder="bar-la-esquina"
              autoCapitalize="none"
              autoCorrect="off"
              aria-invalid={!!errors.tenantSlug}
              {...register("tenantSlug")}
            />
            <FieldDescription>Lo usás para iniciar sesión. Solo minúsculas, números y guiones.</FieldDescription>
            <FieldError>{errors.tenantSlug?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="ownerName">Tu nombre</FieldLabel>
            <Input
              id="ownerName"
              placeholder="Juan Pérez"
              autoComplete="name"
              aria-invalid={!!errors.ownerName}
              {...register("ownerName")}
            />
            <FieldDescription>Opcional. Lo usamos para saludarte en el panel.</FieldDescription>
            <FieldError>{errors.ownerName?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="ownerEmail">Tu email</FieldLabel>
            <Input id="ownerEmail" type="email" autoComplete="email" aria-invalid={!!errors.ownerEmail} {...register("ownerEmail")} />
            <FieldError>{errors.ownerEmail?.message}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="ownerPassword">Contraseña</FieldLabel>
            <Input id="ownerPassword" type="password" autoComplete="new-password" aria-invalid={!!errors.ownerPassword} {...register("ownerPassword")} />
            <FieldError>{errors.ownerPassword?.message}</FieldError>
          </Field>
        </FieldGroup>

        <FormError message={serverError} />

        <Button type="submit" className="w-full" disabled={onboarding.isPending}>
          {onboarding.isPending ? "Creando…" : "Crear comercio"}
        </Button>
      </form>
    </AuthLayout>
  )
}
