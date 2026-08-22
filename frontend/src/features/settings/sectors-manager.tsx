import { useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { SectorDTO, TableDTO } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import {
  useCreateSector,
  useDeleteSector,
  useSectors,
  useUpdateSector,
} from "@/hooks/use-sectors"
import { useTables, useUpdateTable } from "@/hooks/use-tables"

// Config panel (Salones y mesas): CRUD de sectores + asignar cada mesa a un
// sector y su capacidad (default de PAX). Sin sectores → el floor queda plano.
export function SectorsManager() {
  const sectors = useSectors()
  const tables = useTables()
  const createSector = useCreateSector()

  const [name, setName] = useState("")
  const [color, setColor] = useState("#7c9cff")

  const addSector = () => {
    const trimmed = name.trim()
    if (!trimmed) {
      toast.error("Poné un nombre de sector.")
      return
    }
    const nextOrder = (sectors.data?.length ?? 0) + 1
    createSector.mutate(
      { name: trimmed, color, sort_order: nextOrder },
      {
        onSuccess: () => {
          setName("")
          toast.success("Sector creado.")
        },
        onError: (e) =>
          toast.error(isApiError(e) ? e.message : "No pudimos crear el sector."),
      }
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Sectores</h3>
          <p className="text-sm text-muted-foreground">
            Zonas del salón (salón, terraza, barra…) para agrupar las mesas.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <Input
            placeholder="Nombre del sector"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="max-w-[14rem]"
          />
          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            aria-label="Color del sector"
            className="h-9 w-12 cursor-pointer rounded-md border border-border bg-transparent p-1"
          />
          <Button variant="outline" onClick={addSector} disabled={createSector.isPending}>
            Agregar sector
          </Button>
        </div>

        {sectors.isPending ? (
          <Spinner />
        ) : (sectors.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">
            Todavía no hay sectores — el tablero se muestra plano.
          </p>
        ) : (
          <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
            {sectors.data!.map((s) => (
              <SectorRow key={s.id} sector={s} />
            ))}
          </ul>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Mesas y cubiertos</h3>
          <p className="text-sm text-muted-foreground">
            Asigná cada mesa a un sector y su capacidad (default de comensales).
          </p>
        </div>
        {tables.isPending ? (
          <Spinner />
        ) : (tables.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">No hay mesas todavía.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
            {tables.data!.map((t) => (
              <TableAssignRow key={t.id} table={t} sectors={sectors.data ?? []} />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function SectorRow({ sector }: { sector: SectorDTO }) {
  const update = useUpdateSector()
  const remove = useDeleteSector()
  const [name, setName] = useState(sector.name)
  const [color, setColor] = useState(sector.color ?? "#7c9cff")
  const dirty = name.trim() !== sector.name || color !== (sector.color ?? "#7c9cff")

  const save = () => {
    if (!name.trim()) return
    update.mutate(
      { id: sector.id, input: { name: name.trim(), color, sort_order: sector.sort_order } },
      { onError: (e) => toast.error(isApiError(e) ? e.message : "No pudimos guardar.") }
    )
  }

  return (
    <li className="flex flex-wrap items-center gap-2 px-3 py-2.5">
      <input
        type="color"
        value={color}
        onChange={(e) => setColor(e.target.value)}
        aria-label={`Color de ${sector.name}`}
        className="h-8 w-10 shrink-0 cursor-pointer rounded-md border border-border bg-transparent p-1"
      />
      <Input value={name} onChange={(e) => setName(e.target.value)} className="max-w-[12rem]" />
      <div className="ml-auto flex items-center gap-2">
        {dirty ? (
          <Button size="sm" variant="outline" onClick={save} disabled={update.isPending}>
            Guardar
          </Button>
        ) : null}
        <Button
          size="sm"
          variant="ghost"
          className="text-destructive"
          disabled={remove.isPending}
          onClick={() =>
            remove.mutate(sector.id, {
              onError: (e) => toast.error(isApiError(e) ? e.message : "No pudimos borrar."),
            })
          }
        >
          Borrar
        </Button>
      </div>
    </li>
  )
}

function TableAssignRow({ table, sectors }: { table: TableDTO; sectors: SectorDTO[] }) {
  const update = useUpdateTable()
  const [capacity, setCapacity] = useState(table.capacity != null ? String(table.capacity) : "")

  const assignSector = (sectorId: string) => {
    update.mutate(
      { tableId: table.id, patch: { sector_id: sectorId === "" ? null : sectorId } },
      { onError: (e) => toast.error(isApiError(e) ? e.message : "No pudimos asignar.") }
    )
  }

  const saveCapacity = () => {
    const raw = capacity.trim()
    const value = raw === "" ? null : Number(raw)
    if (value !== null && (!Number.isInteger(value) || value < 1)) {
      toast.error("Capacidad inválida.")
      setCapacity(table.capacity != null ? String(table.capacity) : "")
      return
    }
    if (value === table.capacity) return
    update.mutate(
      { tableId: table.id, patch: { capacity: value } },
      { onError: (e) => toast.error(isApiError(e) ? e.message : "No pudimos guardar.") }
    )
  }

  return (
    <li className="flex flex-wrap items-center gap-2 px-3 py-2.5">
      <span className="w-16 shrink-0 text-sm font-medium">
        {table.name ?? `Mesa ${table.number}`}
      </span>
      <select
        value={table.sector_id ?? ""}
        onChange={(e) => assignSector(e.target.value)}
        className="h-9 rounded-md border border-border bg-background px-2 text-sm"
      >
        <option value="">Sin sector</option>
        {sectors.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      <div className="ml-auto flex items-center gap-1.5">
        <Input
          type="number"
          inputMode="numeric"
          placeholder="cap."
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
          onBlur={saveCapacity}
          className="w-20"
        />
        <span className="text-xs text-muted-foreground">cubiertos</span>
      </div>
    </li>
  )
}
