import type { HttpClient } from "@/api/http-client"
import type { CopilotAnswerDTO } from "@/api/types-copilot"

// Data client for the copilot: a natural-language question → grounded answer
// (with the executed SQL + rows as the source). OWNER/MANAGER.
export class CopilotApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  ask(question: string): Promise<CopilotAnswerDTO> {
    return this.http.request<CopilotAnswerDTO>("POST", "/copilot/ask", {
      body: { question },
      auth: true,
    })
  }
}
