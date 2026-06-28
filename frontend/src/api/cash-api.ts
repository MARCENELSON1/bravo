import type { HttpClient } from "@/api/http-client"
import type {
  CashReportDTO,
  CashSessionDTO,
  PaymentMethod,
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
}
