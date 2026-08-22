import { useRef, useState, type ReactNode } from "react"
import { motion } from "motion/react"
import { ArrowLeft, Monitor, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import {
  OverlayScrollbarsComponent,
  type OverlayScrollbarsComponentRef,
} from "overlayscrollbars-react"
import { useNavigate } from "react-router-dom"

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
import { useEdgePeek } from "@/lib/edge-peek"
import { setReduceMotion, useReduceMotion } from "@/lib/reduce-motion"
import { setThemeAnimated } from "@/lib/theme-transition"
import { CommissionRatesCard } from "@/features/finance/commission-rates-card"
import { cn } from "@/lib/utils"

const THEME_OPTIONS = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Oscuro", icon: Moon },
  { value: "system", label: "Sistema", icon: Monitor },
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

const TABS: { id: TabId; label: string; managerOnly?: boolean }[] = [
  { id: "perfil", label: "Mi perfil" },
  { id: "apariencia", label: "Apariencia" },
  { id: "seguridad", label: "Seguridad" },
  { id: "notificaciones", label: "Notificaciones" },
  { id: "facturacion", label: "Facturación electrónica", managerOnly: true },
  { id: "negocio", label: "Datos del local", managerOnly: true },
  { id: "salones", label: "Salones y mesas", managerOnly: true },
  { id: "caja", label: "Caja y pagos", managerOnly: true },
  { id: "comandas", label: "Comandas e impresión", managerOnly: true },
  { id: "equipo", label: "Equipo", managerOnly: true },
  { id: "ia", label: "IA Insights", managerOnly: true },
  { id: "integraciones", label: "Integraciones", managerOnly: true },
  { id: "cuenta", label: "Cuenta", managerOnly: true },
]

type RowDef = {
  label: string
  desc?: string
  required?: boolean
  kind?: "toggle"
  action?: string
  value?: string
  valueKey?: "name" | "email" | "tenant" | "avatar"
}

// Filas por sección. `apariencia` incluye solo los extras (tema y reducir
// movimiento son funcionales y se renderizan aparte). El resto son placeholders.
const SECTIONS: Record<TabId, RowDef[]> = {
  perfil: [
    { label: "Foto de perfil", desc: "Se muestra en tu perfil.", valueKey: "avatar", action: "Cambiar" },
    { label: "Nombre completo", required: true, valueKey: "name" },
    { label: "Email de contacto", required: true, valueKey: "email" },
    { label: "Teléfono", action: "Editar" },
    { label: "Idioma", value: "Español (Argentina)" },
    { label: "Zona horaria", value: "GMT−3 · Buenos Aires" },
    { label: "Formato de hora", value: "24 h" },
    { label: "Pantalla de inicio", desc: "Adónde entrás al abrir la app.", value: "Inicio" },
  ],
  apariencia: [
    { label: "Densidad", desc: "Espaciado de la interfaz.", value: "Cómoda" },
    { label: "Tamaño de texto", value: "Normal" },
    { label: "Color de acento", action: "Elegir" },
    { label: "Alto contraste", kind: "toggle" },
    { label: "Sidebar colapsado", kind: "toggle" },
    { label: "Vista de mesas por defecto", value: "Plano" },
    { label: "Decimales en precios", value: "2" },
  ],
  seguridad: [
    { label: "Contraseña", desc: "Actualizá tu contraseña.", action: "Cambiar" },
    { label: "Verificación en dos pasos (2FA)", kind: "toggle" },
    { label: "PIN de acceso rápido", desc: "Para operar sin re-ingresar.", action: "Configurar" },
    { label: "Bloqueo por inactividad", value: "Desactivado" },
    { label: "Pedir contraseña para anular o descontar", kind: "toggle" },
    { label: "Sesiones activas", action: "Ver" },
    { label: "Historial de accesos", action: "Ver" },
  ],
  notificaciones: [
    { label: "Canales", desc: "Email, push, WhatsApp.", action: "Configurar" },
    { label: "Eventos que avisan", action: "Configurar" },
    { label: "Umbral de mesa demorada", value: "20 min" },
    { label: "Resumen diario", desc: "Y a qué hora te llega.", action: "Configurar" },
    { label: "No molestar", kind: "toggle" },
    { label: "Sonido de alertas", kind: "toggle" },
  ],
  facturacion: [
    { label: "CUIT", required: true, action: "Editar" },
    { label: "Condición frente al IVA", required: true, action: "Editar" },
    { label: "Certificado ARCA", desc: "Certificado y clave fiscal.", action: "Cargar" },
    { label: "Ambiente", desc: "Homologación o producción.", value: "Homologación" },
    { label: "Puntos de venta", action: "Configurar" },
    { label: "Emisión automática al cerrar mesa", kind: "toggle" },
    { label: "Comprobante por defecto", value: "Ticket B" },
    { label: "Envío al cliente", desc: "Comprobante por email o WhatsApp.", action: "Configurar" },
  ],
  negocio: [
    { label: "Nombre", required: true, valueKey: "tenant", action: "Editar" },
    { label: "Logo", action: "Cargar" },
    { label: "Dirección", action: "Editar" },
    { label: "Teléfono", action: "Editar" },
    { label: "Horarios de atención", action: "Configurar" },
    { label: "Capacidad", desc: "Cantidad de cubiertos.", action: "Editar" },
    { label: "Precios con IVA incluido", kind: "toggle" },
    { label: "Redondeo", value: "Sin redondeo" },
    { label: "Cubierto", desc: "Cargo por cubierto.", action: "Configurar" },
    { label: "Propina sugerida", value: "10%" },
  ],
  salones: [
    { label: "Sectores", desc: "Salón, terraza, barra…", action: "Configurar" },
    { label: "Mesas y cubiertos", action: "Configurar" },
    { label: "Numeración automática", kind: "toggle" },
    { label: "Unir y dividir mesas", kind: "toggle" },
  ],
  caja: [
    { label: "Medios de pago", action: "Configurar" },
    { label: "Apertura de caja obligatoria", kind: "toggle" },
    { label: "Arqueo ciego", desc: "Sin ver el esperado al cerrar.", kind: "toggle" },
    { label: "Diferencia tolerada", value: "$0" },
    { label: "Reparto de propinas", action: "Configurar" },
    { label: "Límite de descuento por rol", action: "Configurar" },
    { label: "Cuenta corriente", action: "Configurar" },
  ],
  comandas: [
    { label: "Impresoras por sector", action: "Configurar" },
    { label: "Ruteo de categoría a impresora", action: "Configurar" },
    { label: "Copias", value: "1" },
    { label: "Formato de ticket", action: "Configurar" },
    { label: "Tiempo de alerta del KDS", value: "8 min" },
    { label: "Impresión automática", kind: "toggle" },
  ],
  equipo: [
    { label: "Usuarios", action: "Gestionar" },
    { label: "Roles y permisos", action: "Configurar" },
    { label: "PIN por empleado", action: "Configurar" },
    { label: "Turnos", action: "Configurar" },
    { label: "Tolerancia de fichaje", value: "10 min" },
    { label: "Geocerca", desc: "Fichaje dentro del local.", action: "Configurar" },
  ],
  ia: [
    { label: "Acceso a datos por módulo", action: "Configurar" },
    { label: "Nivel de autonomía", value: "Sugerencias" },
    { label: "Umbrales de alerta", action: "Editar" },
    { label: "Frecuencia del resumen", value: "Diario" },
    { label: "Privacidad", action: "Configurar" },
  ],
  integraciones: [
    { label: "Mercado Pago", action: "Conectar" },
    { label: "PedidosYa", action: "Conectar" },
    { label: "Rappi", action: "Conectar" },
    { label: "WhatsApp", action: "Conectar" },
    { label: "API y webhooks", action: "Configurar" },
  ],
  cuenta: [
    { label: "Plan y uso", desc: "Tu plan de Wellnod.", action: "Ver" },
    { label: "Facturas de Wellnod", action: "Ver" },
    { label: "Exportar datos", action: "Exportar" },
    { label: "Zona de riesgo", desc: "Eliminar cuenta y datos.", action: "Eliminar" },
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

function EditSoon({ label = "Editar" }: { label?: string }) {
  return (
    <button
      type="button"
      disabled
      title="Próximamente"
      className="shrink-0 text-sm font-semibold text-muted-foreground underline underline-offset-4 opacity-60"
    >
      {label}
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
      <OverlayScrollbarsComponent element="div" className="min-h-0" options={OS_OPTIONS_CARD} defer>
        {children}
      </OverlayScrollbarsComponent>
    </GlassCard>
  )
}

// ── Página ────────────────────────────────────────────────────────────────────
export function ConfigPage() {
  const { session } = useAuth()
  const { theme, setTheme } = useTheme()
  const reduceMotion = useReduceMotion()
  const [tab, setTab] = useState<TabId>("perfil")
  const tabsOsRef = useRef<OverlayScrollbarsComponentRef>(null)
  const navigate = useNavigate()
  const [closing, setClosing] = useState(false)
  useEdgePeek(tabsOsRef)

  if (!session) return null

  const canManage = session.role === "OWNER" || session.role === "MANAGER"
  const tabs = TABS.filter((t) => !t.managerOnly || canManage)

  const rowValue = (r: RowDef) =>
    r.valueKey === "name"
      ? (session.name ?? "—")
      : r.valueKey === "email"
        ? session.email
        : r.valueKey === "tenant"
          ? session.tenantName
          : r.value

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
            Inicio
          </button>

          <header className="mb-6 shrink-0">
            <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
              Configuración
            </h1>
            <p className="text-sm text-muted-foreground">Gestioná tus datos y preferencias.</p>
          </header>

          {/* Pestañas (fijas) */}
          <div className="mb-6 shrink-0 border-b border-border">
            <OverlayScrollbarsComponent ref={tabsOsRef} options={OS_OPTIONS_TABS} className="pb-3" defer>
              <div className="flex gap-1">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={cn(
                      "shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap transition duration-200 ease-out active:scale-[0.97]",
                      tab === t.id
                        ? "bg-card text-foreground shadow-sm ring-1 ring-border"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {t.label}
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
                  <Row label="Tema" desc="Apariencia de la interfaz.">
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
                            {opt.label}
                          </button>
                        )
                      })}
                    </div>
                  </Row>
                  <Row label="Reducir movimiento" desc="Desactiva las animaciones de la interfaz.">
                    <span />
                    <LiveSwitch checked={reduceMotion} onChange={setReduceMotion} />
                  </Row>
                </>
              ) : null}

              {/* Comisiones: única fila funcional de Caja y pagos por ahora.
                  Vive acá y no en el Asesor porque afecta también al Inicio y a
                  Finanzas: es un dato del negocio, no un parámetro de una pantalla. */}
              {tab === "caja" ? (
                <div className="py-4">
                  <CommissionRatesCard />
                </div>
              ) : null}

              {/* Filas placeholder de la sección */}
              {SECTIONS[tab].map((r) => {
                const value = rowValue(r)
                return (
                  <Row key={r.label} label={r.label} required={r.required} desc={r.desc}>
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
                      <EditSoon label={r.action} />
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
