import { useState } from "react"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link } from "react-router-dom"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
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

const schema = z.object({
  email: z.email("Email inválido"),
  role: z.enum(["MANAGER", "WAITER", "KITCHEN", "CASHIER"]),
})

type InviteValues = z.infer<typeof schema>

export function InviteUserPage() {
  const invite = useInviteUser()
  const [serverError, setServerError] = useState<string | null>(null)

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
        toast.success("Invitación enviada.")
        reset()
      },
      onError: (error) => {
        if (!isApiError(error)) {
          setServerError("No pudimos enviar la invitación.")
          return
        }
        if (error.code === "email_already_registered" || error.code === "invalid_email") {
          setError("email", { message: error.message })
        } else {
          setServerError(error.message)
        }
      },
    })
  })

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-4 px-6 py-10">
      <Card>
        <CardHeader>
          <CardTitle>Invitar a tu equipo</CardTitle>
          <CardDescription>Le enviamos un email para que cree su cuenta.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input id="email" type="email" aria-invalid={!!errors.email} {...register("email")} />
                <FieldError>{errors.email?.message}</FieldError>
              </Field>

              <Field>
                <FieldLabel htmlFor="role">Rol</FieldLabel>
                <Controller
                  control={control}
                  name="role"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="role" className="w-full">
                        <SelectValue placeholder="Elegí un rol" />
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
            </FieldGroup>

            <FormError message={serverError} />

            <div className="flex items-center justify-between gap-3">
              <Link to="/app" className="text-sm text-muted-foreground underline underline-offset-4">
                Volver
              </Link>
              <Button type="submit" disabled={invite.isPending}>
                {invite.isPending ? "Enviando…" : "Enviar invitación"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
