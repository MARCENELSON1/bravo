import { useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useTranslation } from "react-i18next"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { Check } from "lucide-react"

import { isApiError } from "@/api/api-error"
import { AuthLayout } from "@/components/auth/auth-layout"
import { FormError } from "@/components/form-error"
import { LanguageSwitcher } from "@/components/language-switcher"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useLogin } from "@/hooks/use-login"
import { cn } from "@/lib/utils"

type LoginValues = { slug: string; email: string; password: string }

// "Recordarme": guarda solo el usuario (comercio + email) en el navegador para
// pre-cargarlo la próxima vez. Nunca se guarda la contraseña.
const REMEMBER_KEY = "wellnod:login-remember"

function readRemembered(): { slug: string; email: string } | null {
  try {
    const raw = localStorage.getItem(REMEMBER_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (typeof parsed?.slug === "string" && typeof parsed?.email === "string") {
      return { slug: parsed.slug, email: parsed.email }
    }
  } catch {
    // storage corrupto: lo ignoramos
  }
  return null
}

export function LoginPage() {
  const { t } = useTranslation()
  const login = useLogin()
  const navigate = useNavigate()
  const location = useLocation()
  const [serverError, setServerError] = useState<string | null>(null)
  const [needsVerification, setNeedsVerification] = useState(false)
  const [remembered] = useState(readRemembered)
  const [remember, setRemember] = useState(remembered !== null)

  const schema = useMemo(
    () =>
      z.object({
        slug: z
          .string()
          .min(2, t("login.errors.slugRequired"))
          .regex(/^[a-z0-9-]+$/, t("login.errors.slugFormat")),
        email: z.email(t("login.errors.emailInvalid")),
        password: z.string().min(1, t("login.errors.passwordRequired")),
      }),
    [t]
  )

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      slug: remembered?.slug ?? "",
      email: remembered?.email ?? "",
      password: "",
    },
  })

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    setNeedsVerification(false)
    login.mutate(values, {
      onSuccess: () => {
        if (remember) {
          localStorage.setItem(
            REMEMBER_KEY,
            JSON.stringify({ slug: values.slug, email: values.email })
          )
        } else {
          localStorage.removeItem(REMEMBER_KEY)
        }
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
        setServerError(isApiError(error) ? error.message : t("login.genericError"))
      },
    })
  })

  return (
    <AuthLayout
      title={t("login.title")}
      description={t("login.description")}
      footer={
        <span>
          {t("login.noAccount")}{" "}
          <Link to="/onboarding" className="font-medium text-foreground underline underline-offset-4">
            {t("login.createBusiness")}
          </Link>
        </span>
      }
    >
      <div className="mb-4 flex justify-end">
        <LanguageSwitcher />
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="slug">{t("login.business")}</FieldLabel>
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
            <FieldLabel htmlFor="email">{t("login.email")}</FieldLabel>
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
            <FieldLabel htmlFor="password">{t("login.password")}</FieldLabel>
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

        <div className="-mt-1 flex justify-end">
          <Link
            to="/forgot-password"
            className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
          >
            {t("login.forgotPassword")}
          </Link>
        </div>

        <button
          type="button"
          role="checkbox"
          aria-checked={remember}
          onClick={() => setRemember((v) => !v)}
          className="group flex w-fit cursor-pointer items-center gap-2 text-sm text-muted-foreground outline-none select-none"
        >
          <span
            className={cn(
              "grid size-4 shrink-0 place-items-center rounded-[5px] border transition-all duration-200 ease-out group-focus-visible:ring-2 group-focus-visible:ring-ring/50",
              remember
                ? "border-sidebar-accent bg-sidebar-accent"
                : "border-input bg-transparent dark:bg-input/30"
            )}
          >
            <Check
              className={cn(
                "size-3 text-sidebar-accent-foreground transition-all duration-200 ease-out",
                remember ? "scale-100 opacity-100" : "scale-50 opacity-0"
              )}
            />
          </span>
          {t("login.remember")}
        </button>

        {needsVerification ? (
          <div
            role="alert"
            className="rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm text-foreground"
          >
            {t("login.needsVerification")}
          </div>
        ) : null}

        <FormError message={serverError} />

        <Button
          type="submit"
          className="w-full bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/90"
          disabled={login.isPending}
        >
          {login.isPending ? t("login.submitting") : t("login.submit")}
        </Button>
      </form>
    </AuthLayout>
  )
}
