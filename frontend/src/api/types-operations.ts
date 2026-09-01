// DTOs for Fase 2 (comandas + KDS), mirroring the backend contract.

export type OrderStatus =
  | "OPEN"
  | "SENT"
  | "PREPARING"
  | "READY"
  | "SERVED"
  | "PAID"
  | "CANCELLED"

// Per-item kitchen lifecycle (Fase 14) + the station that prepares it.
export type ItemStatus =
  | "PENDING"
  | "SENT"
  | "PREPARING"
  | "READY"
  | "SERVED"
  | "CANCELLED"
export type Station = "KITCHEN" | "BAR"

export interface ProductDTO {
  id: string
  name: string
  price_amount: number // minor units (e.g. centavos)
  currency: string
  category: string | null
  station: Station
  active: boolean
}

export interface CreateProductResponse {
  product_id: string
}

// --- Carta QR F2 D/E: modificadores de producto -----------------------------

export interface ModifierOptionDTO {
  id: string
  name: string
  price_delta: number // minor units, ≥ 0
}

export interface ModifierGroupDTO {
  id: string
  name: string
  min_select: number
  max_select: number
  required: boolean
  options: ModifierOptionDTO[]
}

export interface ProductModifiersDTO {
  product_id: string
  groups: ModifierGroupDTO[]
}

// Lo que el dueño envía (sin ids — se mintean en el server).
export interface ModifierOptionInput {
  name: string
  price_delta: number
}

export interface ModifierGroupInput {
  name: string
  min_select: number
  max_select: number
  options: ModifierOptionInput[]
}

// --- Carta QR F2 B/E: config del autopedido ---------------------------------

export interface SelfOrderSettingsDTO {
  enabled: boolean
  requires_confirmation: boolean
}

// --- Carta QR F3: config del pago desde la mesa ------------------------------

export interface SelfPaySettingsDTO {
  enabled: boolean
  tips_enabled: boolean
}

// --- Productos v2 Tanda B: precios vs inflación + histórico + rotación --------

export interface PricingRowDTO {
  product_id: string
  product_name: string
  current_price_amount: number
  suggested_price_amount: number
  gap_amount: number
  gap_bps: number
  days_since_change: number
  lagging: boolean
}

export interface PricingInsightsDTO {
  currency: string
  monthly_inflation_bps: number
  configured: boolean
  rows: PricingRowDTO[]
}

export interface PriceChangeDTO {
  changed_at: string // ISO-8601
  old_price_amount: number | null
  new_price_amount: number
}

export interface ProductPriceHistoryDTO {
  product_id: string
  currency: string
  changes: PriceChangeDTO[]
}

export interface WeekdayRotationDTO {
  weekday: number // 0 = Lunes .. 6 = Domingo
  units: number
  sales_amount: number
  top_product_name: string | null
}

export interface ProductRotationDTO {
  currency: string
  rows: WeekdayRotationDTO[]
}

export interface TableDTO {
  id: string
  number: number
  name: string | null
  active: boolean
  sector_id: string | null
  capacity: number | null
}

export interface SectorDTO {
  id: string
  name: string
  color: string | null
  sort_order: number
}

export interface CreateTableResponse {
  table_id: string
}

export interface SelectedOptionDTO {
  option_id: string
  name: string
  price_delta: number
}

export interface OrderItemDTO {
  id: string
  product_id: string
  name: string
  unit_price_amount: number
  quantity: number
  note: string | null
  status: ItemStatus
  station: Station
  sent_at: string | null // ISO-8601; how long the item has waited on the KDS
  // Modificadores elegidos (Carta QR F2). Vacío en la mayoría de las comandas.
  selected_options?: SelectedOptionDTO[]
}

// Origen de la comanda (Carta QR F2): la cargó el mozo o el comensal por QR.
export type OrderSource = "WAITER" | "CUSTOMER_QR"

// One item flattened with its order context — the unit the KDS board renders.
export interface KdsTicket {
  orderId: string
  tableId: string
  item: OrderItemDTO
}

export interface OrderDTO {
  id: string
  table_id: string
  waiter_id: string
  status: OrderStatus
  currency: string
  items: OrderItemDTO[]
  total_amount: number
  source: OrderSource // Carta QR F2: WAITER | CUSTOMER_QR
  created_at: string | null // ISO-8601; used by the KDS waiting timer
  customer_id: string | null // CRM: cliente atribuido a la comanda
}

export interface CreateOrderResponse {
  order_id: string
}

export type SessionState =
  | "OPEN"
  | "IN_KITCHEN"
  | "TO_SERVE"
  | "SERVED"
  | "TO_CHARGE"
  | "CLOSED"

export interface FloorSessionDTO {
  id: string
  state: SessionState // derived live from the visit's orders + signals
  state_since: string | null // ISO-8601; the floor timer runs from here, not created_at
  pax: number | null
  waiter_id: string | null
  waiter_name: string | null
  sector_id: string | null
}

export interface FloorTableDTO {
  id: string
  number: number
  name: string | null
  status: "FREE" | "OCCUPIED"
  active_order: OrderDTO | null
  // Additive session view (state/timer/pax); null → table free or no session.
  session: FloorSessionDTO | null
  // The table's sector (for grouping free tables too) + capacity. null → unassigned.
  sector_id: string | null
  capacity: number | null
}

export interface SessionResponseDTO {
  id: string
  table_id: string
  status: string
  pax: number | null
  waiter_id: string | null
}

export interface BatchOrderItemInput {
  id?: string // client-generated → idempotent
  product_id: string
  quantity: number
  note: string | null
}

// --- Fase 3: pagos (ingresos/egresos) ---

export type PaymentMethod = "CASH" | "CARD" | "TRANSFER" | "MERCADOPAGO" | "QR"
export type PaymentStatus = "PENDING" | "CONFIRMED" | "FAILED" | "REFUNDED"
export type PaymentDirection = "INFLOW" | "OUTFLOW"

export interface PaymentDTO {
  id: string
  direction: PaymentDirection
  order_id: string | null
  method: PaymentMethod
  amount: number // minor units (e.g. centavos)
  tip_amount: number // propina cobrada encima del amount (minor units)
  tax_amount: number // sales tax cobrado DENTRO del amount (minor units), a remitir
  currency: string
  status: PaymentStatus
  category: string | null
  counterparty: string | null
  description: string | null
  // Present only for online charges awaiting confirmation (MercadoPago link/QR).
  checkout_url: string | null
}

export interface TaxCollectedDTO {
  currency: string
  amount: number // sales tax cobrado en la ventana (minor units), a remitir
}

// Estado del outbox de reportes al fisco (TaxJar AutoFile). Todo 0 en AR.
export interface TaxReportStatusDTO {
  pending: number // ventas por reportar (nunca enviadas + último intento fallado)
  failed: number // subset con último intento fallado (necesitan atención)
  sent: number // ya reportadas
}

// Resultado de una corrida del drain (reportar ahora).
export interface TaxReportRunDTO {
  pending: number
  sent: number
  failed: number
}

export interface RegisterPaymentBody {
  method: PaymentMethod
  amount: number // minor units
  tip?: number // propina encima del amount (minor units); 0 si no se manda
  tax?: number // sales tax incluido en amount (minor units); 0 si no se manda
}

export interface RegisterExpenseBody {
  method: PaymentMethod
  amount: number // minor units
  category: string | null
  counterparty: string | null
  description: string | null
}

// --- Fase 3.5: conexión de pasarela por tenant ---

export interface MpConnectionDTO {
  connected: boolean
  nickname: string | null
  external_account_id: string | null
  live_mode: boolean
}

// --- Fase 14: caja / arqueo Z ---

export interface CashSessionDTO {
  id: string
  status: "OPEN" | "CLOSED"
  currency: string
  opening_float_amount: number
  opened_at: string | null
}

export interface CashReportLineDTO {
  method: PaymentMethod
  expected: number // minor units
  tips: number // propina incluida en expected (minor units)
  counted: number | null
  difference: number | null
}

export type CashMovementKind = "DEPOSIT" | "DROP" | "PAYOUT"

export interface CashMovementRowDTO {
  id: string
  kind: CashMovementKind
  amount: number
  signed_amount: number // efecto en el cajón (+ingreso / −salida)
  reason: string | null
  created_at: string | null
}

export interface CashMovementResponseDTO {
  id: string
  kind: CashMovementKind
  amount: number
  signed_amount: number
  currency: string
  reason: string | null
}

export interface CashReportDTO {
  session_id: string
  status: "OPEN" | "CLOSED"
  currency: string
  opening_float: number
  opened_at: string | null
  closed_at: string | null
  lines: CashReportLineDTO[]
  expected_total: number
  counted_total: number | null
  difference_total: number | null
  tips_total: number // total de propinas del turno (para repartir)
  movements: CashMovementRowDTO[]
  cash_in_total: number // Σ ingresos de efectivo
  cash_out_total: number // Σ sangrías + pagos en efectivo
  blind: boolean // arqueo ciego: el esperado va enmascarado mientras OPEN
}

export interface CashSettingsDTO {
  require_open_cash_session: boolean
  blind_cash_count: boolean
}

export interface TipsReportRowDTO {
  waiter_id: string
  waiter_name: string // nombre del mozo (fallback email); nunca el UUID
  earned: number // propina ganada (minor units)
  paid: number // ya liquidado al mozo
  pending: number // earned - paid
}

export interface TipsReportDTO {
  currency: string
  rows: TipsReportRowDTO[]
  earned_total: number
  paid_total: number
  pending_total: number
}

// Guarda D: liquidación en el ledger de propinas (NO es un egreso).
export interface TipPayoutDTO {
  id: string
  waiter_id: string
  amount: number
  currency: string
  method: string
}

// --- Pantalla Finanzas ---

export type FinanceKpiStatus = "healthy" | "warn" | "alert" | "neutral"

export interface FinanceKpiDTO {
  key: string
  kind: "ratio" | "money" | "turnover" // ratio=bps · money=unidad mínima · turnover=centésimas de veces
  value: number
  previous: number
  delta: number
  healthy_low: number | null
  healthy_high: number | null
  status: FinanceKpiStatus
}

export interface FinanceDiagnosticDTO {
  code: string
  severity: string
  bucket: string
  title: string
  body: string
  action: string
}

export interface ProductMarginDTO {
  product_id: string
  product_name: string
  units_sold: number
  sales_amount: number
  margin_amount: number
}

export interface FinanceProjectionDTO {
  sales_amount: number
  net_margin_amount: number
  month_days: number
  elapsed_days: number
}

export interface FinanceOverviewDTO {
  currency: string
  period_days: number
  configured: boolean
  kpis: FinanceKpiDTO[]
  diagnostics: FinanceDiagnosticDTO[]
  product_margins: ProductMarginDTO[]
  summary: string | null
  projection: FinanceProjectionDTO | null
  // Comisiones de pasarela en la ventana + lo cobrado neto de ellas. Línea
  // separada (eje de cobranza), no se mezcla con el margen. 0 si no hay tasas.
  commissions_amount: number
  collected_net_amount: number
}

export interface ExpenseCategoryRowDTO {
  category: string
  amount: number // minor units
  previous: number
  delta: number
}

export interface ExpenseBreakdownDTO {
  currency: string
  total: number
  rows: ExpenseCategoryRowDTO[] // ordenadas por amount desc
}

export interface MovementDTO {
  occurred_at: string // ISO
  kind: "IN" | "OUT"
  amount: number
  method: string
  category: string | null
  description: string | null
  currency: string
}

export interface ProductSaleLineDTO {
  order_id: string
  occurred_at: string
  quantity: number
  line_amount: number
  food_cost_amount: number | null
  margin_amount: number
}

export interface ProductDetailDTO {
  product_id: string
  currency: string
  units_sold: number
  sales_amount: number
  food_cost_amount: number
  margin_amount: number
  lines: ProductSaleLineDTO[]
}

// --- Reporting ---

export interface DashboardSummaryDTO {
  currency: string
  sales: number // minor units
  expenses: number
  net: number
  active_orders: number
  paid_orders: number
  avg_ticket: number
  payment_count: number
  collected_net: number // neto financiero tras comisiones (== sales si no hay tasas)
  fees_total: number // total de comisiones de pasarela
}

// Comisiones (slice B): tasa de comisión por método (bps; 300 = 3%).
export interface FeeRateDTO {
  method: PaymentMethod
  fee_bps: number
}

export interface FeeRatesDTO {
  rates: FeeRateDTO[]
}
