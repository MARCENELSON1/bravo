import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCreateSupplier, useSuppliers } from "@/hooks/use-inventory"

function CreateSupplierSheet() {
  const create = useCreateSupplier()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [contact, setContact] = useState("")

  const submit = () => {
    if (!name.trim()) {
      toast.error("Ingresá un nombre.")
      return
    }
    create.mutate(
      { name: name.trim(), contact: contact.trim() || null },
      {
        onSuccess: () => {
          toast.success("Proveedor creado.")
          setName("")
          setContact("")
          setOpen(false)
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos crear el proveedor."),
      }
    )
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button>Nuevo proveedor</Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Nuevo proveedor</SheetTitle>
          <SheetDescription>Quién te abastece (teléfono, email o referencia).</SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-3 px-4 pb-4">
          <Input placeholder="Nombre" value={name} onChange={(e) => setName(e.target.value)} />
          <Input
            placeholder="Contacto (opcional)"
            value={contact}
            onChange={(e) => setContact(e.target.value)}
          />
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? "Creando…" : "Crear proveedor"}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export function SuppliersPage() {
  const suppliers = useSuppliers()

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-8">
      <header className="flex items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Proveedores
          </GradientHeading>
          <p className="text-sm text-muted-foreground">Tus fuentes de abastecimiento.</p>
        </div>
        <CreateSupplierSheet />
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {suppliers.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : suppliers.data && suppliers.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Contacto</TableHead>
                <TableHead className="text-right">Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {suppliers.data.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell className="text-muted-foreground">{s.contact ?? "—"}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={s.active ? "default" : "secondary"}>
                      {s.active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Todavía no cargaste proveedores.
          </p>
        )}
      </div>
    </div>
  )
}
