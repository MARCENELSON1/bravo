import { useState } from "react"
import { useTranslation } from "react-i18next"
import { MessageCircleQuestion, Sparkles } from "lucide-react"

import { isApiError } from "@/api/api-error"
import { apiErrorText } from "@/api/translate-error"
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

export function CopilotPage() {
  const { t } = useTranslation()
  const examples = t("copilot.examples", { returnObjects: true }) as unknown as string[]
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
      ? apiErrorText(ask.error, t, t("copilot.errorFallback"))
      : null
  const result = ask.data

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          {t("copilot.title")}
        </GradientHeading>
        <p className="text-sm text-muted-foreground">{t("copilot.subtitle")}</p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          submit(question)
        }}
        className="flex gap-2"
      >
        <Input
          placeholder={t("copilot.inputPlaceholder")}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button type="submit" disabled={ask.isPending || !question.trim()}>
          {ask.isPending ? t("copilot.thinking") : t("copilot.ask")}
        </Button>
      </form>

      <div className="flex flex-wrap gap-2">
        {examples.map((ex) => (
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
          <p className="text-muted-foreground">{t("copilot.disabled")}</p>
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
            {showSource ? t("copilot.hideSource") : t("copilot.showSource")}
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
                <p className="text-sm text-muted-foreground">{t("copilot.noRows")}</p>
              )}
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  )
}
