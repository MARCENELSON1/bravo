import { useState } from "react"
import { MessageCircleQuestion, Sparkles } from "lucide-react"

import { isApiError } from "@/api/api-error"
import { Button } from "@/components/ui/button"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useAskCopilot } from "@/hooks/use-copilot"

const EXAMPLES = [
  "¿Cuánto vendí este mes?",
  "¿Cuáles son mis 5 productos más vendidos?",
  "¿Qué mozo facturó más?",
  "¿Cuántas reservas tengo para mañana?",
]

export function CopilotPage() {
  const ask = useAskCopilot()
  const [question, setQuestion] = useState("")
  const [showSource, setShowSource] = useState(false)

  const submit = (q: string) => {
    const text = q.trim()
    if (!text) return
    setShowSource(false)
    ask.mutate(text)
  }

  const disabled =
    ask.isError && isApiError(ask.error) && ask.error.code === "copilot_disabled"
  const errorMessage =
    ask.isError && !disabled
      ? isApiError(ask.error)
        ? ask.error.message
        : "No pudimos responder esa pregunta."
      : null
  const result = ask.data

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Copiloto
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          Preguntá en español sobre tu negocio. Te muestro la respuesta y de dónde sale.
        </p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit(question)
        }}
        className="flex gap-2"
      >
        <Input
          placeholder="¿Cuánto vendí este finde?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button type="submit" disabled={ask.isPending || !question.trim()}>
          {ask.isPending ? "Pensando…" : "Preguntar"}
        </Button>
      </form>

      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <Button
            key={ex}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setQuestion(ex)
              submit(ex)
            }}
          >
            {ex}
          </Button>
        ))}
      </div>

      {disabled ? (
        <div className="flex items-start gap-3 rounded-xl border border-border bg-muted/30 p-4 text-sm">
          <MessageCircleQuestion className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <p className="text-muted-foreground">
            El copiloto todavía no está habilitado en esta cuenta.
          </p>
        </div>
      ) : null}

      {errorMessage ? (
        <p className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {errorMessage}
        </p>
      ) : null}

      {ask.isPending ? (
        <div className="flex justify-center p-10">
          <Spinner className="size-5 text-muted-foreground" />
        </div>
      ) : result ? (
        <section className="flex flex-col gap-3">
          <div className="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4">
            <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
            <p className="text-sm text-foreground">{result.answer}</p>
          </div>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="self-start"
            onClick={() => setShowSource((v) => !v)}
          >
            {showSource ? "Ocultar consulta y datos" : "Ver consulta y datos"}
          </Button>

          {showSource ? (
            <div className="flex flex-col gap-3">
              <pre className="overflow-x-auto rounded-xl border border-border bg-muted/30 p-3 text-xs">
                {result.sql}
              </pre>
              {result.rows.length > 0 ? (
                <div className="overflow-x-auto rounded-xl border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {result.columns.map((c) => (
                          <TableHead key={c}>{c}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.rows.map((row, i) => (
                        <TableRow key={i}>
                          {row.map((cell, j) => (
                            <TableCell key={j} className="tabular-nums">
                              {cell === null ? "—" : String(cell)}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Sin filas.</p>
              )}
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  )
}
