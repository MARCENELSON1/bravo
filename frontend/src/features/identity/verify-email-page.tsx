import { useEffect, useRef } from "react"
import { useTranslation } from "react-i18next"
import { Link, useSearchParams } from "react-router-dom"

import { apiErrorText } from "@/api/translate-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { Spinner } from "@/components/ui/spinner"
import { useVerifyEmail } from "@/hooks/use-verify-email"

export function VerifyEmailPage() {
  const { t } = useTranslation()
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
      {t("identity.goToLogin")}
    </Link>
  )

  if (!token) {
    return (
      <AuthLayout title={t("identity.verifyEmail.invalid.title")} footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          {t("identity.verifyEmail.invalid.body")}
        </p>
      </AuthLayout>
    )
  }

  if (verify.isError) {
    const message = apiErrorText(verify.error, t, t("identity.verifyEmail.error.fallback"))
    return (
      <AuthLayout title={t("identity.verifyEmail.error.title")} footer={loginLink}>
        <p className="text-sm text-muted-foreground">{message}</p>
      </AuthLayout>
    )
  }

  if (verify.isSuccess) {
    return (
      <AuthLayout title={t("identity.verifyEmail.success.title")} footer={loginLink}>
        <p className="text-sm text-muted-foreground">
          {t("identity.verifyEmail.success.body")}
        </p>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title={t("identity.verifyEmail.verifying")}>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Spinner /> {t("identity.verifyEmail.loadingHint")}
      </div>
    </AuthLayout>
  )
}
