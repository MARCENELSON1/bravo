import type { HttpClient } from "@/api/http-client"
import type { CreateProductResponse, ProductDTO, Station } from "@/api/types-operations"

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
}
