import type { HttpClient } from "@/api/http-client"
import type {
  AdjustShiftBody,
  MyTimeclockDTO,
  ShiftDTO,
  ShiftsQuery,
  StaffReportDTO,
} from "@/api/types-timeclock"

// Data client for fichaje: self clock-in/out (toggle) + manager listing,
// corrections and the per-staff report.
export class TimeClockApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  me(): Promise<MyTimeclockDTO> {
    return this.http.request<MyTimeclockDTO>("GET", "/timeclock/me", { auth: true })
  }

  // Toggle: opens a shift if none is open, otherwise closes the open one.
  punch(): Promise<ShiftDTO> {
    return this.http.request<ShiftDTO>("POST", "/timeclock/punch", { auth: true })
  }

  listShifts(query: ShiftsQuery = {}): Promise<ShiftDTO[]> {
    const qs = new URLSearchParams()
    if (query.userId) qs.set("user_id", query.userId)
    if (query.from) qs.set("from", query.from)
    if (query.to) qs.set("to", query.to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return this.http.request<ShiftDTO[]>("GET", `/timeclock/shifts${suffix}`, { auth: true })
  }

  adjustShift(shiftId: string, body: AdjustShiftBody): Promise<ShiftDTO> {
    return this.http.request<ShiftDTO>("PATCH", `/timeclock/shifts/${shiftId}`, {
      body,
      auth: true,
    })
  }

  staffReport(query: { from?: string; to?: string } = {}): Promise<StaffReportDTO> {
    const qs = new URLSearchParams()
    if (query.from) qs.set("from", query.from)
    if (query.to) qs.set("to", query.to)
    const suffix = qs.toString() ? `?${qs.toString()}` : ""
    return this.http.request<StaffReportDTO>("GET", `/reports/staff${suffix}`, { auth: true })
  }
}
