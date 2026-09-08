import type { ReactNode } from "react"
import { motion } from "motion/react"
import { useTranslation } from "react-i18next"
import { Check } from "lucide-react"

import { AppBackground } from "@/components/shell/app-background"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { useReduceMotion } from "@/lib/reduce-motion"
import { cn } from "@/lib/utils"

// Shell de las pantallas de identidad (login, alta de comercio, invitación,
// verificación, recuperar y restablecer contraseña). Tocar esto las re-skinea a
// todas.
//
// Antes era un split con un panel verde y una textura fotográfica encima: un
// lenguaje visual que no existía ni en la app ni en la landing, así que entrar a
// Wellnod se sentía como llegar a otro producto. Ahora usa las mismas tres piezas
// que el resto: el fondo escénico neutro, el vidrio de los paneles y el verde
// reservado para la marca y los acentos.
//
// La columna de la izquierda repite el título del hero de la landing y sus tres
// grupos de producto: quien viene de la web reconoce la promesa con la que entró.

// El wordmark, con la misma receta que la navbar de la landing.
function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-heading text-3xl tracking-tight text-foreground", className)}>
      <span className="font-bold">Well</span>
      <span className="-ml-[2px] font-light text-foreground/55">nod</span>
    </span>
  )
}

const BULLETS = ["shift", "business", "decisions"] as const

export function AuthLayout({
  title,
  description,
  children,
  footer,
  variant = "default",
  enter = true,
}: {
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
  /**
   * "wide" ensancha la tarjeta y le cede ancho a su columna, para los formularios
   * largos (el alta de comercio). El relato de marca se queda en su lugar.
   */
  variant?: "default" | "wide"
  /**
   * La animación de entrada de la tarjeta. Se apaga cuando se llega desde otra
   * pantalla de identidad que ya la animó: si no, la tarjeta termina de crecer y
   * acto seguido se desvanece y vuelve, que es el parpadeo que se veía.
   */
  enter?: boolean
}) {
  const reduce = useReduceMotion()
  const { t } = useTranslation()

  return (
    <div className="relative min-h-svh">
      <AppBackground />

      <div
        data-wide={variant === "wide"}
        className="auth-grid mx-auto min-h-svh max-w-6xl items-center px-5 py-10"
      >
        {/* Relato de marca. Se esconde en pantallas angostas: ahí el formulario es
            todo lo que importa y el discurso ya lo leyeron en la landing. */}
        <motion.section
          className="hidden flex-col lg:flex"
          initial={reduce || !enter ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduce ? { duration: 0 } : { duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <Wordmark />

          <h1 className="font-heading mt-10 text-4xl font-bold tracking-tight text-balance text-foreground">
            {t("auth.brandTitleBefore")}
            <span className="text-primary">{t("auth.brandTitleHighlight")}</span>.
          </h1>
          <p className="mt-4 max-w-md text-base text-muted-foreground">
            {t("auth.brandSubtitle")}
          </p>

          <ul className="mt-8 flex max-w-md flex-col gap-3">
            {BULLETS.map((key) => (
              <li key={key} className="flex gap-3">
                <Check className="mt-1 size-4 shrink-0 text-primary" />
                <p className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">
                    {t(`auth.bullets.${key}.label`)}
                  </span>
                  {" — "}
                  {t(`auth.bullets.${key}.text`)}
                </p>
              </li>
            ))}
          </ul>
        </motion.section>

        {/* Formulario */}
        <motion.main
          className="auth-card"
          initial={reduce || !enter ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={reduce ? { duration: 0 } : { duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
        >
          {/* En angosto el wordmark encabeza el formulario; en ancho ya está en la
              columna de marca y repetirlo sería decir la marca dos veces. */}
          <div className="mb-6 flex justify-center lg:hidden">
            <Wordmark />
          </div>

          <GlassCard className="p-6 sm:p-8">
            <div className="mb-6 flex flex-col gap-1">
              <GradientHeading size="sm" weight="bold">
                {title}
              </GradientHeading>
              {description ? (
                <p className="text-sm text-muted-foreground">{description}</p>
              ) : null}
            </div>
            {children}
          </GlassCard>

          {footer ? (
            <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>
          ) : null}
        </motion.main>
      </div>
    </div>
  )
}
