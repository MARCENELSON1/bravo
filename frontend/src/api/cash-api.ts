import type { HttpClient } from "@/api/http-client"
import type {
  CashReportDTO,
  CashSessionDTO,
  PaymentDTO,
  PaymentMethod,
  TipsReportDTO,
} from "@/api/types-operations"

// Caja / arqueo Z (Fase 14): open a register turn, read the live esperado, and
// close it with a per-method count.
export class CashApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  open(openingFloatAmount: number, note?: string | null): Promise<CashSessionDTO> {
    return this.http.request<CashSessionDTO>("POST", "/cashier/session/open", {
      body: { opening_float_amount: openingFloatAmount, note: note ?? null },
      auth: true,
    })
  }

  // The live arqueo of the open session, or null when none is open.
  current(): Promise<CashReportDTO | null> {
    return this.http.request<CashReportDTO | null>("GET", "/cashier/session/current", {
      auth: true,
    })
  }

  close(
    sessionId: string,
    counted: Partial<Record<PaymentMethod, number>>,
    note?: string | null
  ): Promise<CashReportDTO> {
    return this.http.request<CashReportDTO>("POST", `/cashier/session/${sessionId}/close`, {
      body: { counted, note: note ?? null },
      auth: true,
    })
  }

  // Propinas ganadas vs liquidadas por mozo en [from, to) (ISO; default = todo).
  tipsReport(from?: string, to?: string): Promise<TipsReportDTO> {
    const params = new URLSearchParams()
    if (from) params.set("from", from)
    if (to) params.set("to", to)
    const qs = params.toString()
    return this.http.request<TipsReportDTO>(
      "GET",
      `/cashier/tips/report${qs ? `?${qs}` : ""}`,
      { auth: true }
    )
  }

  // Liquidar propinas a un mozo (egreso 'Propinas' a su nombre).
  payTip(waiterId: string, amount: number): Promise<PaymentDTO> {
    return this.http.request<PaymentDTO>("POST", "/cashier/tips/payout", {
      body: { waiter_id: waiterId, amount },
      auth: true,
    })
  }
}
