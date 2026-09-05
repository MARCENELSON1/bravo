import { useState, type ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
import type { SupplierDTO } from "@/api/types-inventory"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
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
  useCreateSupplier,
  useSupplierPurchases,
  useSuppliers,
  useUpdateSupplier,
} from "@/hooks/use-inventory"
import { formatMoney } from "@/lib/money"
import { waLink } from "@/lib/wa"

function SupplierFormSheet({
  supplier,
  trigger,
}: {
  supplier?: SupplierDTO
  trigger: ReactNode
}) {
  const { t } = useTranslation()
  const create = useCreateSupplier()
  const update = useUpdateSupplier()
  const editing = supplier != null
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(supplier?.name ?? "")
  const [contact, setContact] = useState(supplier?.contact ?? "")
  const [phone, setPhone] = useState(supplier?.phone ?? "")
  const [notes, setNotes] = useState(supplier?.notes ?? "")
  const pending = create.isPending || update.isPending

  const submit = () => {
    if (!name.trim()) {
      toast.error(t("inventory.suppliers.invalidName"))
      return
    }
    const body = {
      name: name.trim(),
      contact: contact.trim() || null,
      phone: phone.trim() || null,
      notes: notes.trim() || null,
    }
    const onError = (error: unknown) =>
      toast.error(apiErrorText(error, t, t("inventory.suppliers.saveError")))
    const onSuccess = () => {
      toast.success(
        editing ? t("inventory.suppliers.updateSuccess") : t("inventory.suppliers.createSuccess")
      )
      setOpen(false)
      if (!editing) {
        setName("")
        setContact("")
        setPhone("")
        setNotes("")
      }
    }
    if (editing) {
      update.mutate({ id: supplier.id, body: { ...body, active: supplier.active } }, { onSuccess, onError })
    } else {
      create.mutate(body, { onSuccess, onError })
    }
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>{trigger}</SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>
            {editing
              ? t("inventory.suppliers.editTitle", { name: supplier.name })
              : t("inventory.suppliers.createTitle")}
          </SheetTitle>
          <SheetDescription>{t("inventory.suppliers.formDescription")}</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input
            placeholder={t("inventory.suppliers.namePlaceholder")}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Input
            placeholder={t("inventory.suppliers.contactPlaceholder")}
            value={contact}
            onChange={(e) => setContact(e.target.value)}
          />
          <Input
            placeholder={t("inventory.suppliers.phonePlaceholder")}
            inputMode="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <Input
            placeholder={t("inventory.suppliers.notesPlaceholder")}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <Button onClick={submit} disabled={pending}>
            {pending
              ? t("inventory.suppliers.saving")
              : editing
                ? t("inventory.suppliers.save")
                : t("inventory.suppliers.createSubmit")}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

function SupplierRow({ supplier }: { supplier: SupplierDTO }) {
  const { t } = useTranslation()
  const [showPurchases, setShowPurchases] = useState(false)
  const purchases = useSupplierPurchases(showPurchases ? supplier.id : null)
  // Preferí el teléfono estructurado; si no hay, caé a los dígitos del contacto
  // (proveedores viejos con el teléfono en el campo libre). waLink filtra: un email
  // en contacto no tiene dígitos → sin botón (correcto).
  const link = waLink(supplier.phone ?? supplier.contact, t("inventory.suppliers.waMessage"))

  return (
    <GlassCard className="flex flex-col gap-2 p-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-foreground">{supplier.name}</span>
            {!supplier.active ? (
              <Badge variant="secondary" className="text-xs font-normal">
                {t("inventory.suppliers.inactive")}
              </Badge>
            ) : null}
          </div>
          {supplier.contact ? (
            <p className="text-sm text-muted-foreground">{supplier.contact}</p>
          ) : null}
          {supplier.phone ? (
            <p className="text-sm text-muted-foreground">{supplier.phone}</p>
          ) : null}
          {supplier.notes ? (
            <p className="truncate text-xs text-muted-foreground">{supplier.notes}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => setShowPurchases((v) => !v)}>
            {showPurchases ? t("inventory.suppliers.hide") : t("inventory.suppliers.purchases")}
          </Button>
          <SupplierFormSheet
            supplier={supplier}
            trigger={
              <Button size="sm" variant="ghost">
                {t("inventory.suppliers.edit")}
              </Button>
            }
          />
          {link ? (
            <a href={link} target="_blank" rel="noopener noreferrer">
              <Button size="sm" variant="outline">
                {t("inventory.suppliers.whatsapp")}
              </Button>
            </a>
          ) : null}
        </div>
      </div>
      {showPurchases ? (
        <div className="border-t pt-2 text-sm">
          {purchases.isPending ? (
            <span className="text-muted-foreground">{t("inventory.suppliers.loading")}</span>
          ) : purchases.data && purchases.data.purchase_count > 0 ? (
            <span className="text-foreground">
              <span className="font-medium">{purchases.data.purchase_count}</span>{" "}
              {t("inventory.suppliers.purchasesWord", { count: purchases.data.purchase_count })} ·{" "}
              <span className="font-medium">
                {formatMoney(purchases.data.total_spent, purchases.data.currency)}
              </span>{" "}
              {t("inventory.suppliers.inTotal")}
              {purchases.data.last_purchase_at
                ? ` · ${t("inventory.suppliers.lastLabel")}: ${purchases.data.last_purchase_at.slice(0, 10)}`
                : ""}
            </span>
          ) : (
            <span className="text-muted-foreground">
              {t("inventory.suppliers.noPurchases")}
            </span>
          )}
        </div>
      ) : null}
    </GlassCard>
  )
}

export function SuppliersPage() {
  const { t } = useTranslation()
  const suppliers = useSuppliers()
  const rows = suppliers.data ?? []

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            {t("inventory.suppliers.title")}
          </GradientHeading>
          <p className="text-sm text-muted-foreground">
            {t("inventory.suppliers.subtitle")}
          </p>
        </div>
        <SupplierFormSheet trigger={<Button>{t("inventory.suppliers.newSupplier")}</Button>} />
      </header>

      {suppliers.isPending ? (
        <div className="flex justify-center p-10">
          <Spinner className="size-5 text-muted-foreground" />
        </div>
      ) : rows.length === 0 ? (
        <EmptyState className="rounded-xl border border-border">
          {t("inventory.suppliers.emptyState")}
        </EmptyState>
      ) : (
        <div className="flex flex-col gap-2">
          {rows.map((s) => (
            <SupplierRow key={s.id} supplier={s} />
          ))}
        </div>
      )}
    </div>
  )
}
