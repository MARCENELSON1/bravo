import { useRef, useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { motion } from "motion/react"
import { ArrowLeft, Monitor, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import {
  OverlayScrollbarsComponent,
  type OverlayScrollbarsComponentRef,
} from "overlayscrollbars-react"
import { useNavigate } from "react-router-dom"

import { edgeFadeClass, useEdgeFade } from "@/lib/edge-fade"
import { SCROLL_FADE_EVENTS } from "@/lib/scroll-fade"
import { hourCycleLabel, timeZoneLabel } from "@/lib/format"

// Tab bar horizontal: siempre visible y un gris un poco más oscuro.
const OS_OPTIONS_TABS = {
  scrollbars: { theme: "os-theme-wellnod-static", autoHide: "never" },
} as const

// Cuadro de sección: la barra no se esconde (queda visible mientras haya contenido
// para scrollear) y usa el mismo gris que la barra horizontal de las pestañas.
const OS_OPTIONS_CARD = {
  scrollbars: { theme: "os-theme-wellnod-static", autoHide: "never" },
} as const

import { useAuth } from "@/auth/auth-context"
import { AppBackground } from "@/components/shell/app-background"
import { GlassCard } from "@/components/ui/glass-card"
import { InviteUserForm } from "@/features/identity/invite-user-page"
import { IntegrationsPanel } from "@/features/integrations/integrations-page"
import { setReduceMotion, useReduceMotion } from "@/lib/reduce-motion"
import { setThemeAnimated } from "@/lib/theme-transition"
import { CommissionRatesCard } from "@/features/finance/commission-rates-card"
import { CashSettingsCard } from "@/features/settings/cash-settings-card"
import { FiscalAddressCard } from "@/features/settings/fiscal-address-card"
import { TaxJarConnectionCard } from "@/features/settings/taxjar-connection-card"
import { SectorsManager } from "@/features/settings/sectors-manager"
import { cn } from "@/lib/utils"

// `label` guarda la clave i18n; el consumidor la resuelve con t(). `value` es el
// código del tema (light/dark/system), no cambia.
const THEME_OPTIONS = [
  { value: "light", label: "settings.themeOptions.light", icon: Sun },
  { value: "dark", label: "settings.themeOptions.dark", icon: Moon },
  { value: "system", label: "settings.themeOptions.system", icon: Monitor },
] as const

type TabId =
  | "perfil"
  | "apariencia"
  | "seguridad"
  | "notificaciones"
  | "facturacion"
  | "negocio"
  | "salones"
  | "caja"
  | "comandas"
  | "equipo"
  | "ia"
  | "integraciones"
  | "cuenta"

// `label` guarda la clave i18n del tab; se resuelve con t() al renderizar.
const TABS: { id: TabId; label: string; managerOnly?: boolean }[] = [
  { id: "perfil", label: "settings.tabs.perfil" },
  { id: "apariencia", label: "settings.tabs.apariencia" },
  { id: "seguridad", label: "settings.tabs.seguridad" },
  { id: "notificaciones", label: "settings.tabs.notificaciones" },
  { id: "facturacion", label: "settings.tabs.facturacion", managerOnly: true },
  { id: "negocio", label: "settings.tabs.negocio", managerOnly: true },
  { id: "salones", label: "settings.tabs.salones", managerOnly: true },
  { id: "caja", label: "settings.tabs.caja", managerOnly: true },
  { id: "comandas", label: "settings.tabs.comandas", managerOnly: true },
  { id: "equipo", label: "settings.tabs.equipo", managerOnly: true },
  { id: "ia", label: "settings.tabs.ia", managerOnly: true },
  { id: "integraciones", label: "settings.tabs.integraciones", managerOnly: true },
  { id: "cuenta", label: "settings.tabs.cuenta", managerOnly: true },
]

type RowDef = {
  label: string
  desc?: string
  required?: boolean
  kind?: "toggle"
  action?: string
  value?: string
  valueKey?: "name" | "email" | "tenant" | "avatar" | "language" | "timezone" | "timeFormat"
}

// Filas por sección. `apariencia` incluye solo los extras (tema y reducir
// movimiento son funcionales y se renderizan aparte). El resto son placeholders.
// `label`/`desc`/`value`/`action` guardan claves i18n; se resuelven con t() al
// renderizar. Los slugs y los códigos (valueKey, kind) no cambian.
const SECTIONS: Record<TabId, RowDef[]> = {
  perfil: [
    { label: "settings.rows.perfil.avatar.label", desc: "settings.rows.perfil.avatar.desc", valueKey: "avatar", action: "settings.actions.edit" },
    { label: "settings.rows.perfil.name.label", required: true, valueKey: "name" },
    { label: "settings.rows.perfil.email.label", required: true, valueKey: "email" },
    { label: "settings.rows.perfil.phone.label", action: "settings.actions.edit" },
    { label: "settings.rows.perfil.language.label", valueKey: "language" },
    { label: "settings.rows.perfil.timezone.label", valueKey: "timezone" },
    { label: "settings.rows.perfil.timeFormat.label", valueKey: "timeFormat" },
    { label: "settings.rows.perfil.homeScreen.label", desc: "settings.rows.perfil.homeScreen.desc", value: "settings.rows.perfil.homeScreen.value" },
  ],
  apariencia: [
    { label: "settings.rows.apariencia.density.label", desc: "settings.rows.apariencia.density.desc", value: "settings.rows.apariencia.density.value" },
    { label: "settings.rows.apariencia.textSize.label", value: "settings.rows.apariencia.textSize.value" },
    { label: "settings.rows.apariencia.accentColor.label", action: "settings.actions.choose" },
    { label: "settings.rows.apariencia.highContrast.label", kind: "toggle" },
    { label: "settings.rows.apariencia.collapsedSidebar.label", kind: "toggle" },
    { label: "settings.rows.apariencia.defaultTableView.label", value: "settings.rows.apariencia.defaultTableView.value" },
    { label: "settings.rows.apariencia.priceDecimals.label", value: "settings.rows.apariencia.priceDecimals.value" },
  ],
  seguridad: [
    { label: "settings.rows.seguridad.password.label", desc: "settings.rows.seguridad.password.desc", action: "settings.actions.change" },
    { label: "settings.rows.seguridad.twoFactor.label", kind: "toggle" },
    { label: "settings.rows.seguridad.pin.label", desc: "settings.rows.seguridad.pin.desc", action: "settings.actions.configure" },
    { label: "settings.rows.seguridad.inactivityLock.label", value: "settings.rows.seguridad.inactivityLock.value" },
    { label: "settings.rows.seguridad.passwordForVoid.label", kind: "toggle" },
    { label: "settings.rows.seguridad.activeSessions.label", action: "settings.actions.view" },
    { label: "settings.rows.seguridad.accessHistory.label", action: "settings.actions.view" },
  ],
  notificaciones: [
    { label: "settings.rows.notificaciones.channels.label", desc: "settings.rows.notificaciones.channels.desc", action: "settings.actions.configure" },
    { label: "settings.rows.notificaciones.events.label", action: "settings.actions.configure" },
    { label: "settings.rows.notificaciones.delayedTableThreshold.label", value: "settings.rows.notificaciones.delayedTableThreshold.value" },
    { label: "settings.rows.notificaciones.dailySummary.label", desc: "settings.rows.notificaciones.dailySummary.desc", action: "settings.actions.configure" },
    { label: "settings.rows.notificaciones.doNotDisturb.label", kind: "toggle" },
    { label: "settings.rows.notificaciones.alertSound.label", kind: "toggle" },
  ],
  facturacion: [
    { label: "settings.rows.facturacion.cuit.label", required: true, action: "settings.actions.edit" },
    { label: "settings.rows.facturacion.ivaCondition.label", required: true, action: "settings.actions.edit" },
    { label: "settings.rows.facturacion.arcaCertificate.label", desc: "settings.rows.facturacion.arcaCertificate.desc", action: "settings.actions.upload" },
    { label: "settings.rows.facturacion.environment.label", desc: "settings.rows.facturacion.environment.desc", value: "settings.rows.facturacion.environment.value" },
    { label: "settings.rows.facturacion.salesPoints.label", action: "settings.actions.configure" },
    { label: "settings.rows.facturacion.autoIssue.label", kind: "toggle" },
    { label: "settings.rows.facturacion.defaultReceipt.label", value: "settings.rows.facturacion.defaultReceipt.value" },
    { label: "settings.rows.facturacion.sendToCustomer.label", desc: "settings.rows.facturacion.sendToCustomer.desc", action: "settings.actions.configure" },
  ],
  negocio: [
    { label: "settings.rows.negocio.name.label", required: true, valueKey: "tenant", action: "settings.actions.edit" },
    { label: "settings.rows.negocio.logo.label", action: "settings.actions.upload" },
    { label: "settings.rows.negocio.address.label", action: "settings.actions.edit" },
    { label: "settings.rows.negocio.phone.label", action: "settings.actions.edit" },
    { label: "settings.rows.negocio.hours.label", action: "settings.actions.configure" },
    { label: "settings.rows.negocio.capacity.label", desc: "settings.rows.negocio.capacity.desc", action: "settings.actions.edit" },
    { label: "settings.rows.negocio.vatIncluded.label", kind: "toggle" },
    { label: "settings.rows.negocio.rounding.label", value: "settings.rows.negocio.rounding.value" },
    { label: "settings.rows.negocio.coverCharge.label", desc: "settings.rows.negocio.coverCharge.desc", action: "settings.actions.configure" },
    { label: "settings.rows.negocio.suggestedTip.label", value: "settings.rows.negocio.suggestedTip.value" },
  ],
  salones: [
    { label: "settings.rows.salones.sectors.label", desc: "settings.rows.salones.sectors.desc", action: "settings.actions.configure" },
    { label: "settings.rows.salones.tables.label", action: "settings.actions.configure" },
    { label: "settings.rows.salones.autoNumbering.label", kind: "toggle" },
    { label: "settings.rows.salones.mergeSplit.label", kind: "toggle" },
  ],
  caja: [
    { label: "settings.rows.caja.paymentMethods.label", action: "settings.actions.configure" },
    { label: "settings.rows.caja.requireOpenCash.label", kind: "toggle" },
    { label: "settings.rows.caja.blindCount.label", desc: "settings.rows.caja.blindCount.desc", kind: "toggle" },
    { label: "settings.rows.caja.toleratedDifference.label", value: "settings.rows.caja.toleratedDifference.value" },
    { label: "settings.rows.caja.tipSharing.label", action: "settings.actions.configure" },
    { label: "settings.rows.caja.discountLimit.label", action: "settings.actions.configure" },
    { label: "settings.rows.caja.houseAccount.label", action: "settings.actions.configure" },
  ],
  comandas: [
    { label: "settings.rows.comandas.printersBySector.label", action: "settings.actions.configure" },
    { label: "settings.rows.comandas.categoryRouting.label", action: "settings.actions.configure" },
    { label: "settings.rows.comandas.copies.label", value: "settings.rows.comandas.copies.value" },
    { label: "settings.rows.comandas.ticketFormat.label", action: "settings.actions.configure" },
    { label: "settings.rows.comandas.kdsAlertTime.label", value: "settings.rows.comandas.kdsAlertTime.value" },
    { label: "settings.rows.comandas.autoPrint.label", kind: "toggle" },
  ],
  equipo: [
    { label: "settings.rows.equipo.users.label", action: "settings.actions.manage" },
    { label: "settings.rows.equipo.rolesPermissions.label", action: "settings.actions.configure" },
    { label: "settings.rows.equipo.pinPerEmployee.label", action: "settings.actions.configure" },
    { label: "settings.rows.equipo.shifts.label", action: "settings.actions.configure" },
    { label: "settings.rows.equipo.clockInTolerance.label", value: "settings.rows.equipo.clockInTolerance.value" },
    { label: "settings.rows.equipo.geofence.label", desc: "settings.rows.equipo.geofence.desc", action: "settings.actions.configure" },
  ],
  ia: [
    { label: "settings.rows.ia.dataAccess.label", action: "settings.actions.configure" },
    { label: "settings.rows.ia.autonomyLevel.label", value: "settings.rows.ia.autonomyLevel.value" },
    { label: "settings.rows.ia.alertThresholds.label", action: "settings.actions.edit" },
    { label: "settings.rows.ia.summaryFrequency.label", value: "settings.rows.ia.summaryFrequency.value" },
    { label: "settings.rows.ia.privacy.label", action: "settings.actions.configure" },
  ],
  integraciones: [
    { label: "settings.rows.integraciones.mercadopago.label", action: "settings.actions.connect" },
    { label: "settings.rows.integraciones.pedidosya.label", action: "settings.actions.connect" },
    { label: "settings.rows.integraciones.rappi.label", action: "settings.actions.connect" },
    { label: "settings.rows.integraciones.whatsapp.label", action: "settings.actions.connect" },
    { label: "settings.rows.integraciones.apiWebhooks.label", action: "settings.actions.configure" },
  ],
  cuenta: [
    { label: "settings.rows.cuenta.planUsage.label", desc: "settings.rows.cuenta.planUsage.desc", action: "settings.actions.view" },
    { label: "settings.rows.cuenta.invoices.label", action: "settings.actions.view" },
    { label: "settings.rows.cuenta.exportData.label", action: "settings.actions.export" },
    { label: "settings.rows.cuenta.riskZone.label", desc: "settings.rows.cuenta.riskZone.desc", action: "settings.actions.delete" },
  ],
}

// ── Sub-componentes ───────────────────────────────────────────────────────────
function Switch({ checked, disabled }: { checked: boolean; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors",
        checked ? "bg-primary" : "bg-black/15 dark:bg-white/25",
        disabled ? "cursor-not-allowed opacity-70" : "cursor-pointer"
      )}
    >
      <span
        className={cn(
          "inline-block size-5 rounded-full bg-white shadow ring-1 ring-black/10 transition-transform",
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        )}
      />
    </button>
  )
}

function LiveSwitch({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition-colors",
        checked ? "bg-primary" : "bg-black/15 dark:bg-white/25"
      )}
    >
      <span
        className={cn(
          "inline-block size-5 rounded-full bg-white shadow ring-1 ring-black/10 transition-transform",
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        )}
      />
    </button>
  )
}

function Row({
  label,
  required,
  desc,
  children,
}: {
  label: string
  required?: boolean
  desc?: string
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-3 py-5 md:flex-row md:items-center md:justify-between md:gap-6">
      <div className="md:w-80 md:shrink-0">
        <p className="text-sm font-medium text-foreground">
          {label}
          {required ? <span className="text-primary"> *</span> : null}
        </p>
        {desc ? <p className="mt-0.5 text-sm text-muted-foreground">{desc}</p> : null}
      </div>
      <div className="flex flex-1 items-center justify-between gap-4">{children}</div>
    </div>
  )
}

function EditSoon({ label }: { label?: string }) {
  const { t } = useTranslation()
  return (
    <button
      type="button"
      disabled
      title={t("settings.editSoon")}
      className="shrink-0 text-sm font-semibold text-muted-foreground underline underline-offset-4 opacity-60"
    >
      {label ?? t("settings.actions.edit")}
    </button>
  )
}

const initialsOf = (name: string | null, email: string) => {
  if (name) {
    const parts = name.trim().split(/\s+/)
    return (
      ((parts[0]?.[0] ?? "") + (parts.length > 1 ? (parts.at(-1)?.[0] ?? "") : "")).toUpperCase() ||
      email[0]?.toUpperCase() ||
      "?"
    )
  }
  return email[0]?.toUpperCase() || "?"
}

// Cuadro de sección con scroll interno: solo scrollea su propio contenido (y solo
// cuando no entra en el alto disponible), en vez de scrollear la página entera.
function ScrollCard({ children }: { children: ReactNode }) {
  return (
    <GlassCard className="flex max-h-full flex-col overflow-hidden">
      <OverlayScrollbarsComponent
        element="div"
        className="scroll-fade min-h-0"
        options={OS_OPTIONS_CARD}
        events={SCROLL_FADE_EVENTS}
        defer
      >
        {children}
      </OverlayScrollbarsComponent>
    </GlassCard>
  )
}

// ── Página ────────────────────────────────────────────────────────────────────
export function ConfigPage() {
  const { t, i18n } = useTranslation()
  const { session } = useAuth()
  const { theme, setTheme } = useTheme()
  const reduceMotion = useReduceMotion()
  const [tab, setTab] = useState<TabId>("perfil")
  const navigate = useNavigate()
  const tabsOsRef = useRef<OverlayScrollbarsComponentRef>(null)
  const tabEdges = useEdgeFade(tabsOsRef)
  const [closing, setClosing] = useState(false)

  if (!session) return null

  const canManage = session.role === "OWNER" || session.role === "MANAGER"
  const tabs = TABS.filter((item) => !item.managerOnly || canManage)

  const rowValue = (r: RowDef) =>
    r.valueKey === "name"
      ? (session.name ?? "—")
      : r.valueKey === "email"
        ? session.email
        : r.valueKey === "tenant"
          ? session.tenantName
          : r.valueKey === "language"
            ? t(`settings.languageNames.${i18n.language?.startsWith("en") ? "en" : "es"}`)
            : r.valueKey === "timezone"
              ? timeZoneLabel()
              : r.valueKey === "timeFormat"
                ? hourCycleLabel()
                : r.value
                  ? t(r.value)
                  : undefined

  return (
    <div className="h-svh overflow-hidden">
      <AppBackground />
      <motion.div
        className="h-svh"
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: closing ? 0 : 1 }}
        transition={{ duration: reduceMotion ? 0 : 0.3, ease: "easeInOut" }}
        onAnimationComplete={() => {
          if (closing) navigate("/app")
        }}
      >
        <div className="mx-auto flex h-full w-full max-w-4xl flex-col px-4 py-6 sm:px-6 sm:py-8">
          <button
            type="button"
            onClick={() => setClosing(true)}
            className="mb-5 inline-flex shrink-0 items-center gap-1.5 self-start rounded-lg text-sm font-medium text-muted-foreground transition duration-200 ease-out hover:text-foreground active:scale-[0.97]"
          >
            <ArrowLeft className="size-4" />
            {t("settings.back")}
          </button>

          <header className="mb-6 shrink-0">
            <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
              {t("settings.title")}
            </h1>
            <p className="text-sm text-muted-foreground">{t("settings.subtitle")}</p>
          </header>

          {/* Pestañas (fijas) */}
          <div className="mb-6 shrink-0 border-b border-border">
            <OverlayScrollbarsComponent
              ref={tabsOsRef}
              options={OS_OPTIONS_TABS}
              className={cn("pb-3", edgeFadeClass(tabEdges))}
              defer
            >
              <div className="flex gap-1">
                {tabs.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setTab(item.id)}
                    className={cn(
                      "relative shrink-0 rounded-xl px-3 py-2.5 text-sm font-medium whitespace-nowrap transition duration-200 ease-out active:scale-[0.97]",
                      tab === item.id
                        ? "text-sidebar-accent-foreground"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent/15 hover:text-sidebar-foreground"
                    )}
                  >
                    {tab === item.id ? (
                      <motion.span
                        initial={reduceMotion ? false : { opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={reduceMotion ? { duration: 0 } : { duration: 0.15, ease: "easeOut" }}
                        className="absolute inset-0 rounded-xl bg-sidebar-accent shadow-sm"
                      />
                    ) : null}
                    <span className="relative z-10">{t(item.label)}</span>
                  </button>
                ))}
              </div>
            </OverlayScrollbarsComponent>
          </div>

          {/* Contenido: solo el cuadro scrollea, y solo si no entra */}
          <motion.div
            key={tab}
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: reduceMotion ? 0 : 0.2, ease: "easeOut" }}
            className="min-h-0 flex-1"
          >
            {tab === "equipo" ? (
              <ScrollCard>
                <div className="px-4 sm:px-6">
                  <InviteUserForm embedded />
                </div>
              </ScrollCard>
            ) : tab === "integraciones" ? (
              <ScrollCard>
                <div className="px-4 sm:px-6">
                  <IntegrationsPanel embedded />
                </div>
              </ScrollCard>
            ) : (
              <ScrollCard>
                <div className="divide-y divide-border px-4 sm:px-6">
                  {/* Apariencia: filas funcionales primero */}
                  {tab === "apariencia" ? (
                <>
                  <Row label={t("settings.appearance.theme")} desc={t("settings.appearance.themeDesc")}>
                    <div className="flex flex-wrap gap-2">
                      {THEME_OPTIONS.map((opt) => {
                        const active = theme === opt.value
                        return (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => setThemeAnimated(setTheme, opt.value)}
                            aria-pressed={active}
                          className={cn(
                              "flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition duration-200 ease-out active:scale-[0.97]",
                              active
                                ? "border-primary bg-primary/10 text-foreground"
                                : "border-border text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                          )}
                        >
                            <opt.icon className="size-4" />
                            {t(opt.label)}
                        </button>
                        )
                      })}
                    </div>
                  </Row>
                  <Row label={t("settings.appearance.reduceMotion")} desc={t("settings.appearance.reduceMotionDesc")}>
                    <span />
                    <LiveSwitch checked={reduceMotion} onChange={setReduceMotion} />
                  </Row>
                </>
              ) : null}

              {/* Comisiones: única fila funcional de Caja y pagos por ahora.
                  Vive acá y no en el Asesor porque afecta también al Inicio y a
                  Finanzas: es un dato del negocio, no un parámetro de una pantalla. */}
              {tab === "caja" ? (
                <div className="flex flex-col gap-4 py-4">
                  <CashSettingsCard />
                  <CommissionRatesCard />
                </div>
              ) : null}

              {/* Salones: CRUD real de sectores + asignación de mesas. */}
              {tab === "salones" ? (
                <div className="py-4">
                  <SectorsManager />
                </div>
              ) : null}

              {/* Datos del local: dirección fiscal real (la usa el motor de
                  impuestos US/TaxJar). El resto son placeholders. */}
              {tab === "negocio" ? (
                <div className="py-4">
                  <FiscalAddressCard />
                  <TaxJarConnectionCard />
                </div>
              ) : null}

              {/* Filas placeholder de la sección (en Salones, las de Sectores y
                  Mesas ya son reales arriba → se ocultan). */}
              {SECTIONS[tab]
                .filter(
                  (r) =>
                    tab !== "salones" ||
                    (r.label !== "settings.rows.salones.sectors.label" &&
                      r.label !== "settings.rows.salones.tables.label")
                )
                .filter(
                  (r) =>
                    tab !== "caja" ||
                    (r.label !== "settings.rows.caja.requireOpenCash.label" &&
                      r.label !== "settings.rows.caja.blindCount.label")
                )
                .filter((r) => tab !== "negocio" || r.label !== "settings.rows.negocio.address.label")
                .map((r) => {
                const value = rowValue(r)
                return (
                  <Row key={r.label} label={t(r.label)} required={r.required} desc={r.desc ? t(r.desc) : undefined}>
                    {r.valueKey === "avatar" ? (
                      <span className="grid size-12 shrink-0 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                        {initialsOf(session.name, session.email)}
                      </span>
                    ) : value ? (
                      <span className="truncate text-foreground">{value}</span>
                    ) : (
                      <span />
                  )}
                    {r.kind === "toggle" ? (
                      <Switch checked={false} disabled />
                    ) : (
                      <EditSoon label={r.action ? t(r.action) : undefined} />
                  )}
                  </Row>
                )
              })}
                </div>
              </ScrollCard>
            )}
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}
