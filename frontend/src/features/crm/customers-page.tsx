import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { CustomerDTO, CustomerInput } from "@/api/customers-api"
import { useAuth } from "@/auth/auth-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useCreateCustomer,
  useCustomers,
  useDeleteCustomer,
  useUpdateCustomer,
} from "@/hooks/use-customers"
import { waLink } from "@/lib/wa"

export function CustomersPage() {
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
          <GradientHeading>Clientes</GradientHeading>
          <p className="text-sm text-muted-foreground">
            Tu cartera de clientes. Contactalos por WhatsApp con un toque.
          </p>
        </div>
        {canManage ? (
          <Button onClick={() => setAdding((v) => !v)} variant={adding ? "outline" : "default"}>
            {adding ? "Cancelar" : "Nuevo cliente"}
          </Button>
        ) : null}
      </header>

      {adding ? (
        <CustomerForm
          title="Nuevo cliente"
          onCancel={() => setAdding(false)}
          onSaved={() => setAdding(false)}
        />
      ) : null}

      <Input
        placeholder="Buscar por nombre o teléfono…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {customers.isPending ? (
        <Spinner />
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {search ? "No hay clientes que coincidan." : "Todavía no cargaste clientes."}
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {rows.map((c) =>
            editing === c.id ? (
              <CustomerForm
                key={c.id}
                title={`Editar ${c.name}`}
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
  const del = useDeleteCustomer()
  const link = customer.no_contactar ? null : waLink(customer.phone, `Hola ${customer.name}!`)

  return (
    <GlassCard className="flex flex-wrap items-center gap-3 p-4">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground">{customer.name}</span>
          {customer.no_contactar ? (
            <Badge variant="secondary" className="text-xs font-normal">
              No contactar
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
        {link ? (
          <a href={link} target="_blank" rel="noopener noreferrer">
            <Button size="sm" variant="outline">
              WhatsApp
            </Button>
          </a>
        ) : null}
        {canManage ? (
          <>
            <Button size="sm" variant="ghost" onClick={onEdit}>
              Editar
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="text-destructive"
              disabled={del.isPending}
              onClick={() => {
                if (!window.confirm(`¿Borrar a ${customer.name}?`)) return
                del.mutate(customer.id, {
                  onError: (e) =>
                    toast.error(isApiError(e) ? e.message : "No pudimos borrar el cliente."),
                })
              }}
            >
              Borrar
            </Button>
          </>
        ) : null}
      </div>
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
      toast.error("Poné un nombre.")
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
      toast.error(isApiError(e) ? e.message : "No pudimos guardar el cliente.")
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
        <Input placeholder="Nombre *" value={name} onChange={(e) => setName(e.target.value)} />
        <Input
          placeholder="Teléfono (con código país)"
          inputMode="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <Input
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input placeholder="Notas" value={notes} onChange={(e) => setNotes(e.target.value)} />
      </div>
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          checked={noContactar}
          onChange={(e) => setNoContactar(e.target.checked)}
        />
        No contactar (opt-out) — no se ofrece el botón de WhatsApp
      </label>
      <div className="flex gap-2">
        <Button onClick={submit} disabled={pending}>
          Guardar
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </GlassCard>
  )
}
