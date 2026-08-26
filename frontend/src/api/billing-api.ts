import type { HttpClient } from "@/api/http-client"
import type {
  BillingPlanDTO,
  CheckoutResponseDTO,
  SubscriptionDTO,
} from "@/api/types-billing"

// Data client de la suscripción del SaaS (lado tenant/owner).
export class BillingApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  plans(region: string): Promise<BillingPlanDTO[]> {
    return this.http.request<BillingPlanDTO[]>(
      "GET",
      `/billing/plans?region=${encodeURIComponent(region)}`,
      { auth: true }
    )
  }

  subscription(): Promise<SubscriptionDTO | null> {
    return this.http.request<SubscriptionDTO | null>("GET", "/billing/subscription", {
      auth: true,
    })
  }

  checkout(planId: string): Promise<CheckoutResponseDTO> {
    return this.http.request<CheckoutResponseDTO>("POST", "/billing/checkout", {
      body: { plan_id: planId },
      auth: true,
    })
  }

  cancel(): Promise<void> {
    return this.http.request<void>("DELETE", "/billing/subscription", { auth: true })
  }
}
