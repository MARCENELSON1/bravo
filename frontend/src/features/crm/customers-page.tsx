import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import type { CustomerDTO, CustomerInput } from "@/api/customers-api"
import { apiErrorText } from "@/api/translate-error"
import { useAuth } from "@/auth/auth-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useCreateCustomer,
  useCustomerHistory,
  useCustomers,
  useDeleteCustomer,
  useUpdateCustomer,
} from "@/hooks/use-customers"
import { CustomerActionsView } from "@/features/crm/customer-actions-view"
import { CustomerSegmentsView } from "@/features/crm/customer-segments-view"
import { formatMoney } from "@/lib/money"
import { waLink } from "@/lib/wa"

export function CustomersPage() {
  const { t } = useTranslation()
  const { session } = useAuth()
  const canManage = session?.role === "OWNER" || session?.role === "MANAGER"
  const [search, setSearch] = useState("")
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState<string | null>(null)
  const customers = useCustomers(search.trim() || undefined)
  const rows = customers.data ?? []

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <GradientHeading>{t("crm.title")}</GradientHeading>
          <p className="text-sm text-muted-foreground">{t("crm.subtitle")}</p>
        </div>
        {canManage ? (
          <Button onClick={() => setAdding((v) => !v)} variant={adding ? "outline" : "default"}>
            {adding ? t("crm.cancel") : t("crm.newCustomer")}
          </Button>
        ) : null}
      </header>

      {adding ? (
        <CustomerForm
          title={t("crm.newCustomer")}
          onCancel={() => setAdding(false)}
          onSaved={() => setAdding(false)}
        />
      ) : null}

      <CustomerActionsView />

      <CustomerSegmentsView />

      <Input
        placeholder={t("crm.searchPlaceholder")}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {customers.isPending ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {search ? t("crm.noMatches") : t("crm.empty")}
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {rows.map((c) =>
            editing === c.id ? (
              <CustomerForm
                key={c.id}
                title={t("crm.editName", { name: c.name })}
                customer={c}
                onCancel={() => setEditing(null)}
                onSaved={() => setEditing(null)}
              />
            ) : (
              <CustomerRow
                key={c.id}
                customer={c}
                canManage={canManage}
                onEdit={() => setEditing(c.id)}
              />
            )
          )}
        </div>
      )}
    </div>
  )
}

function CustomerRow({
  customer,
  canManage,
  onEdit,
}: {
  customer: CustomerDTO
  canManage: boolean
  onEdit: () => void
}) {
  const { t } = useTranslation()
  const del = useDeleteCustomer()
  const [showHistory, setShowHistory] = useState(false)
  const history = useCustomerHistory(showHistory ? customer.id : null)
  const link = customer.no_contactar
    ? null
    : waLink(customer.phone, t("crm.waGreeting", { name: customer.name }))

  return (
    <GlassCard className="flex flex-col gap-2 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-foreground">{customer.name}</span>
            {customer.no_contactar ? (
              <Badge variant="secondary" className="text-xs font-normal">
                {t("crm.noContactBadge")}
              </Badge>
            ) : null}
          </div>
          {customer.phone ? (
            <p className="text-sm text-muted-foreground">{customer.phone}</p>
          ) : null}
          {customer.notes ? (
            <p className="truncate text-xs text-muted-foreground">{customer.notes}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => setShowHistory((v) => !v)}>
            {showHistory ? t("crm.hide") : t("crm.history")}
          </Button>
          {link ? (
            <a href={link} target="_blank" rel="noopener noreferrer">
              <Button size="sm" variant="outline">
                {t("crm.whatsapp")}
              </Button>
            </a>
          ) : null}
          {canManage ? (
            <>
              <Button size="sm" variant="ghost" onClick={onEdit}>
                {t("crm.edit")}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive"
                disabled={del.isPending}
                onClick={() => {
                  if (!window.confirm(t("crm.confirmDelete", { name: customer.name }))) return
                  del.mutate(customer.id, {
                    onError: (e) =>
                      toast.error(apiErrorText(e, t, t("crm.deleteError"))),
                  })
                }}
              >
                {t("crm.delete")}
              </Button>
            </>
          ) : null}
        </div>
      </div>
      {showHistory ? (
        <div className="border-t pt-2 text-sm">
          {history.isPending ? (
            <span className="text-muted-foreground">{t("crm.loading")}</span>
          ) : history.data ? (
            history.data.visits === 0 ? (
              <span className="text-muted-foreground">
                {t("crm.historyDetail.noPurchases")}
              </span>
            ) : (
              <span className="text-foreground">
                <span className="font-medium">{history.data.visits}</span>{" "}
                {t("crm.visitWord", { count: history.data.visits })} ·{" "}
                <span className="font-medium">
                  {formatMoney(history.data.total_spent, history.data.currency)}
                </span>{" "}
                {t("crm.spent")}
                {history.data.last_visit_at
                  ? t("crm.historyDetail.lastVisit", {
                      date: history.data.last_visit_at.slice(0, 10),
                    })
                  : ""}
              </span>
            )
          ) : (
            <span className="text-muted-foreground">{t("crm.historyDetail.loadError")}</span>
          )}
        </div>
      ) : null}
    </GlassCard>
  )
}

function CustomerForm({
  title,
  customer,
  onCancel,
  onSaved,
}: {
  title: string
  customer?: CustomerDTO
  onCancel: () => void
  onSaved: () => void
}) {
  const { t } = useTranslation()
  const create = useCreateCustomer()
  const update = useUpdateCustomer()
  const [name, setName] = useState(customer?.name ?? "")
  const [phone, setPhone] = useState(customer?.phone ?? "")
  const [email, setEmail] = useState(customer?.email ?? "")
  const [notes, setNotes] = useState(customer?.notes ?? "")
  const [noContactar, setNoContactar] = useState(customer?.no_contactar ?? false)
  const pending = create.isPending || update.isPending

  const submit = () => {
    if (!name.trim()) {
      toast.error(t("crm.form.nameRequired"))
      return
    }
    const input: CustomerInput = {
      name: name.trim(),
      phone: phone.trim() || null,
      email: email.trim() || null,
      notes: notes.trim() || null,
      no_contactar: noContactar,
    }
    const onError = (e: unknown) =>
      toast.error(apiErrorText(e, t, t("crm.form.saveError")))
    if (customer) {
      update.mutate({ id: customer.id, input }, { onSuccess: onSaved, onError })
    } else {
      create.mutate(input, { onSuccess: onSaved, onError })
    }
  }

  return (
    <GlassCard className="flex flex-col gap-3 p-5">
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <Input
          placeholder={t("crm.form.namePlaceholder")}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Input
          placeholder={t("crm.form.phonePlaceholder")}
          inputMode="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <Input
          placeholder={t("crm.form.emailPlaceholder")}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          placeholder={t("crm.form.notesPlaceholder")}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={noContactar}
          onChange={(e) => setNoContactar(e.target.checked)}
        />
        {t("crm.form.noContact")}
      </label>
      <div className="flex gap-2">
        <Button onClick={submit} disabled={pending}>
          {t("crm.save")}
        </Button>
        <Button variant="outline" onClick={onCancel}>
          {t("crm.cancel")}
        </Button>
      </div>
    </GlassCard>
  )
}
