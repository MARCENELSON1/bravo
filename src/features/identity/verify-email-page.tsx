import { useEffect, useRef } from "react"
import { Link, useSearchParams } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { Spinner } from "@/components/ui/spinner"
import { useVerifyEmail } from "@/hooks/use-verify-email"

export function VerifyEmailPage() {
  const [params] = useSearchParams()
  const token = params.get("token")
  const verify = useVerifyEmail()
  const started = useRef(false)

  useEffect(() => {
    if (started.current || !token) return
    started.current = true
    verify.mutate(token)
  }, [token, verify])

  const loginLink = (
    <Link to="/login" className="font-medium text-foreground underline underline-offset-4">
      Ir a iniciar sesión
    </Link>
  )

  if (!token) {
    return (
      <AuthLayout title="Enlace inválido" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          El enlace de verificación no es válido. Pedí uno nuevo desde tu email.
        </p>
      </AuthLayout>
    )
  }

  if (verify.isError) {
    const message = isApiError(verify.error)
      ? verify.error.message
      : "No pudimos verificar tu email."
    return (
      <AuthLayout title="No pudimos verificar" footer={loginLink}>
        <p className="text-sm text-muted-foreground">{message}</p>
      </AuthLayout>
    )
  }

  if (verify.isSuccess) {
    return (
      <AuthLayout title="Email verificado" footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          Tu email quedó verificado. Ya podés iniciar sesión.
        </p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Verificando tu email">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Spinner /> Un momento…
      </div>
    </AuthLayout>
  )
}
