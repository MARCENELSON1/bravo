import type { InvoiceStatus } from "@/api/types-invoicing"
import { Badge } from "@/components/ui/badge"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  INVOICE_STATUS_LABELS,
  invoiceNumber,
  invoiceTypeLabel,
} from "@/lib/invoice-labels"
import { formatMoney } from "@/lib/money"
import { useInvoices } from "@/hooks/use-invoices"

const STATUS_VARIANT: Record<InvoiceStatus, "default" | "secondary" | "destructive"> = {
  AUTHORIZED: "default",
  DRAFT: "secondary",
  REJECTED: "destructive",
}

export function InvoicesPage() {
  const invoices = useInvoices()

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 px-6 py-8">
      <header className="flex flex-col gap-1">
        <GradientHeading size="md" weight="bold">
          Comprobantes
        </GradientHeading>
        <p className="text-sm text-muted-foreground">
          Facturas electrónicas emitidas (AFIP). El CAE es la autorización fiscal.
        </p>
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {invoices.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : invoices.data && invoices.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Comprobante</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>CAE</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.data.map((inv) => (
                <TableRow key={inv.id}>
                  <TableCell className="font-medium tabular-nums">
                    {invoiceNumber(inv.point_of_sale, inv.number)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {invoiceTypeLabel(inv.type)}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {inv.cae ?? "—"}
                    {inv.cae_expiration ? (
                      <span className="block">vto. {inv.cae_expiration}</span>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[inv.status]}>
                      {INVOICE_STATUS_LABELS[inv.status]}
                    </Badge>
                    {inv.rejection ? (
                      <span className="block text-xs text-destructive">{inv.rejection}</span>
                    ) : null}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(inv.total, inv.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Todavía no emitiste comprobantes. Facturá una comanda pagada desde su detalle.
          </p>
        )}
      </div>
    </div>
  )
}
