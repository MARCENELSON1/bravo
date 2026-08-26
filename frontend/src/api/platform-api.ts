import type { HttpClient } from "@/api/http-client"
import type {
  FeatureDTO,
  PlatformAccessDTO,
  PlatformPlanDTO,
  PlatformPlanInput,
} from "@/api/types-platform"

// Data client del panel de plataforma. `access` lo puede llamar cualquier usuario
// (para mostrar/ocultar el panel); el resto está gateado a super-admin en el back.
export class PlatformApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  access(): Promise<PlatformAccessDTO> {
    return this.http.request<PlatformAccessDTO>("GET", "/platform/access", { auth: true })
  }

  features(): Promise<FeatureDTO[]> {
    return this.http.request<FeatureDTO[]>("GET", "/platform/features", { auth: true })
  }

  listPlans(): Promise<PlatformPlanDTO[]> {
    return this.http.request<PlatformPlanDTO[]>("GET", "/platform/plans", { auth: true })
  }

  savePlan(body: PlatformPlanInput): Promise<PlatformPlanDTO> {
    return this.http.request<PlatformPlanDTO>("POST", "/platform/plans", { body, auth: true })
  }

  deletePlan(id: string): Promise<void> {
    return this.http.request<void>("DELETE", `/platform/plans/${id}`, { auth: true })
  }
}
