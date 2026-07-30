import type { HttpClient } from "@/api/http-client"
import type {
  ExpenseBreakdownDTO,
  FinanceOverviewDTO,
  MovementDTO,
  ProductDetailDTO,
} from "@/api/types-operations"

export interface FinanceQuery {
  from?: string // ISO
  to?: string // ISO
}

// Data client de la Pantalla Finanzas: un solo payload con los KPIs vitales,
// comparativo, diagnósticos y margen por producto.
export class FinanceApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  overview(query: FinanceQuery = {}): Promise<FinanceOverviewDTO> {
    return this.http.request<FinanceOverviewDTO>(
      "GET",
      `/finance/overview${this.qs(query)}`,
      { auth: true }
    )
  }

  // Drill-down: las líneas de venta de un producto en la ventana.
  productDetail(productId: string, query: FinanceQuery = {}): Promise<ProductDetailDTO> {
    return this.http.request<ProductDetailDTO>(
      "GET",
      `/finance/products/${productId}${this.qs(query)}`,
      { auth: true }
    )
  }

  // Egresos por categoría en la ventana + comparativo con el período previo.
  expenseBreakdown(query: FinanceQuery = {}): Promise<ExpenseBreakdownDTO> {
    return this.http.request<ExpenseBreakdownDTO>(
      "GET",
      `/finance/expenses/breakdown${this.qs(query)}`,
      { auth: true }
    )
  }

  // Últimos movimientos (cobros + egresos) en la ventana.
  recentMovements(query: FinanceQuery = {}): Promise<MovementDTO[]> {
    return this.http.request<MovementDTO[]>(
      "GET",
      `/finance/movements${this.qs(query)}`,
      { auth: true }
    )
  }

  private qs(query: FinanceQuery): string {
    const params = new URLSearchParams()
    if (query.from) params.set("from", query.from)
    if (query.to) params.set("to", query.to)
    const s = params.toString()
    return s ? `?${s}` : ""
  }
}
