import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
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
        },
        onError: (error) =>
          setServerError(isApiError(error) ? error.message : "No pudimos crear el producto."),
      }
    )
  })

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Productos
        </GradientHeading>
        <p className="text-sm text-muted-foreground">Tu catálogo y precios.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Nuevo producto</CardTitle>
          <CardDescription>El precio se ingresa en la moneda del comercio.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="flex flex-col gap-4" noValidate>
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Catálogo</CardTitle>
        </CardHeader>
        <CardContent>
          {products.isPending ? (
            <Spinner />
          ) : products.data && products.data.length > 0 ? (
            <ul className="flex flex-col divide-y divide-border">
              {products.data.map((p) => (
                <li key={p.id} className="flex items-center justify-between py-2 text-sm">
                  <span className="text-foreground">
                    {p.name}
                    {p.category ? (
                      <span className="text-muted-foreground"> · {p.category}</span>
                    ) : null}
                  </span>
                  <span className="font-medium">{formatMoney(p.price_amount, p.currency)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Todavía no cargaste productos.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
