export interface CopilotAnswerDTO {
  answer: string
  sql: string // la consulta ejecutada (fuente)
  columns: string[]
  rows: unknown[][]
  llm_enabled: boolean
}

export interface AskCopilotBody {
  question: string
}
