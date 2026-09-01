import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { PaymentMethod } from "@/api/types-operations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useExpenses, useRegisterExpense } from "@/hooks/use-payments"
import { formatMoney } from "@/lib/money"

const EXPENSE_METHODS: PaymentMethod[] = ["CASH", "TRANSFER", "CARD", "MERCADOPAGO"]

export function ExpensesPage() {
  const { t } = useTranslation()
  const expenses = useExpenses()
  const registerExpense = useRegisterExpense()
  const [open, setOpen] = useState(false)
  const [method, setMethod] = useState<PaymentMethod>("CASH")
  const [amount, setAmount] = useState("")
  const [category, setCategory] = useState("")
  const [counterparty, setCounterparty] = useState("")
  const [description, setDescription] = useState("")

  const submit = () => {
    const minor = Math.round(Number(amount) * 100)
    if (!Number.isFinite(minor) || minor < 1) {
      toast.error(t("expenses.form.invalidAmount"))
      return
    }
    registerExpense.mutate(
      {
        method,
        amount: minor,
        category: category.trim() || null,
        counterparty: counterparty.trim() || null,
        description: description.trim() || null,
      },
      {
        onSuccess: () => {
          toast.success(t("expenses.form.success"))
          setAmount("")
          setCategory("")
          setCounterparty("")
          setDescription("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("expenses.form.error"))),
      }
    )
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("expenses.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">{t("expenses.subtitle")}</p>
        </div>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button>{t("expenses.new")}</Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>{t("expenses.new")}</SheetTitle>
              <SheetDescription>{t("expenses.form.description")}</SheetDescription>
            </SheetHeader>
            <div className="flex flex-col gap-3 px-4 pb-4">
              <div className="flex items-end gap-2">
                <Select value={method} onValueChange={(v) => setMethod(v as PaymentMethod)}>
                  <SelectTrigger className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EXPENSE_METHODS.map((m) => (
                      <SelectItem key={m} value={m}>
                        {t(`expenses.methodLabels.${m}`)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder={t("expenses.form.amountPlaceholder")}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="max-w-[8rem]"
                />
              </div>
              <Input
                placeholder={t("expenses.form.categoryPlaceholder")}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
              <Input
                placeholder={t("expenses.form.counterpartyPlaceholder")}
                value={counterparty}
                onChange={(e) => setCounterparty(e.target.value)}
              />
              <Input
                placeholder={t("expenses.form.descriptionPlaceholder")}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
              <Button onClick={submit} disabled={registerExpense.isPending}>
                {registerExpense.isPending
                  ? t("expenses.form.submitting")
                  : t("expenses.form.submit")}
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {expenses.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : expenses.data && expenses.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("expenses.table.counterparty")}</TableHead>
                <TableHead>{t("expenses.table.category")}</TableHead>
                <TableHead>{t("expenses.table.method")}</TableHead>
                <TableHead className="text-right">{t("expenses.table.amount")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {expenses.data.map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="font-medium">
                    {e.counterparty ?? "—"}
                    {e.description ? (
                      <span className="block text-xs font-normal text-muted-foreground">
                        {e.description}
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{e.category ?? "—"}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {t(`expenses.methodLabels.${e.method}`, { defaultValue: e.method })}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(e.amount, e.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <EmptyState>
            {t("expenses.empty")}
          </EmptyState>
        )}
      </div>
    </div>
  )
}
