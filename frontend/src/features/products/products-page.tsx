import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { FormError } from "@/components/form-error"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
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
import { useCreateProduct, useProducts } from "@/hooks/use-products"
import { formatMoney } from "@/lib/money"

const schema = z.object({
  name: z.string().min(1, "Ingresá un nombre").max(120),
  price: z
    .string()
    .min(1, "Ingresá un precio")
    .refine((v) => Number(v) > 0, "El precio debe ser mayor a 0"),
  category: z.string().max(60).optional(),
})

type ProductValues = z.infer<typeof schema>

export function ProductsPage() {
  const products = useProducts()
  const createProduct = useCreateProduct()
  const [open, setOpen] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", price: "", category: "" },
  })

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    createProduct.mutate(
      {
        name: values.name,
        priceAmount: Math.round(Number(values.price) * 100),
        category: values.category ? values.category : null,
      },
      {
        onSuccess: () => {
          toast.success("Producto creado.")
          reset()
          setOpen(false)
        },
        onError: (error) =>
          setServerError(isApiError(error) ? error.message : "No pudimos crear el producto."),
      }
    )
  })

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 px-6 py-8">
      <header className="flex items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Productos
          </GradientHeading>
          <p className="text-sm text-muted-foreground">Tu catálogo y precios.</p>
        </div>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button>Nuevo producto</Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Nuevo producto</SheetTitle>
              <SheetDescription>El precio se ingresa en la moneda del comercio.</SheetDescription>
            </SheetHeader>
            <form onSubmit={onSubmit} className="flex flex-col gap-4 px-4 pb-4" noValidate>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="name">Nombre</FieldLabel>
                  <Input id="name" aria-invalid={!!errors.name} {...register("name")} />
                  <FieldError>{errors.name?.message}</FieldError>
                </Field>
                <Field>
                  <FieldLabel htmlFor="price">Precio</FieldLabel>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    inputMode="decimal"
                    aria-invalid={!!errors.price}
                    {...register("price")}
                  />
                  <FieldError>{errors.price?.message}</FieldError>
                </Field>
                <Field>
                  <FieldLabel htmlFor="category">Categoría (opcional)</FieldLabel>
                  <Input id="category" {...register("category")} />
                </Field>
              </FieldGroup>
              <FormError message={serverError} />
              <Button type="submit" disabled={createProduct.isPending}>
                {createProduct.isPending ? "Creando…" : "Crear producto"}
              </Button>
            </form>
          </SheetContent>
        </Sheet>
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {products.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : products.data && products.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Categoría</TableHead>
                <TableHead className="text-right">Precio</TableHead>
                <TableHead className="text-right">Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.data.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell className="text-muted-foreground">{p.category ?? "—"}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(p.price_amount, p.currency)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant={p.active ? "default" : "secondary"}>
                      {p.active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Todavía no cargaste productos.
          </p>
        )}
      </div>
    </div>
  )
}
