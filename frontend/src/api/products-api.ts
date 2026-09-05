import type { HttpClient } from "@/api/http-client"
import type { AnalyticsQuery } from "@/api/types-analytics"
import type {
  CreateProductResponse,
  ModifierGroupInput,
  PricingInsightsDTO,
  ProductDTO,
  ProductModifiersDTO,
  ProductPriceHistoryDTO,
  ProductRotationDTO,
  Station,
} from "@/api/types-operations"

export class ProductsApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  list(): Promise<ProductDTO[]> {
    return this.http.request<ProductDTO[]>("GET", "/products", { auth: true })
  }

  create(
    name: string,
    priceAmount: number,
    category: string | null,
    station: Station = "KITCHEN"
  ): Promise<CreateProductResponse> {
    return this.http.request<CreateProductResponse>("POST", "/products", {
      body: { name, price_amount: priceAmount, category, station },
      auth: true,
    })
  }

  // --- Productos v2 Tanda B ---------------------------------------------------

  updatePrice(productId: string, priceAmount: number): Promise<ProductDTO> {
    return this.http.request<ProductDTO>("PUT", `/products/${productId}/price`, {
      body: { price_amount: priceAmount },
      auth: true,
    })
  }

  pricing(): Promise<PricingInsightsDTO> {
    return this.http.request<PricingInsightsDTO>("GET", "/products/pricing", {
      auth: true,
    })
  }

  priceHistory(productId: string): Promise<ProductPriceHistoryDTO> {
    return this.http.request<ProductPriceHistoryDTO>(
      "GET",
      `/products/${productId}/price-history`,
      { auth: true }
    )
  }

  // --- Carta QR F2 D/E: modificadores ----------------------------------------

  // Grupos de TODOS los productos activos en un batch: la comanda los precarga
  // con el catálogo para que los chips salgan al instante al tocar un plato.
  menuModifiers(): Promise<ProductModifiersDTO[]> {
    return this.http.request<ProductModifiersDTO[]>("GET", "/products/modifiers", {
      auth: true,
    })
  }

  modifiers(productId: string): Promise<ProductModifiersDTO> {
    return this.http.request<ProductModifiersDTO>(
      "GET",
      `/products/${productId}/modifiers`,
      { auth: true }
    )
  }

  setModifiers(productId: string, groups: ModifierGroupInput[]): Promise<ProductModifiersDTO> {
    return this.http.request<ProductModifiersDTO>(
      "PUT",
      `/products/${productId}/modifiers`,
      { body: { groups }, auth: true }
    )
  }

  rotation(query: AnalyticsQuery = {}): Promise<ProductRotationDTO> {
    const params = new URLSearchParams()
    if (query.from) params.set("from", query.from)
    if (query.to) params.set("to", query.to)
    const qs = params.toString()
    return this.http.request<ProductRotationDTO>(
      "GET",
      `/products/rotation${qs ? `?${qs}` : ""}`,
      { auth: true }
    )
  }
}
