import { useState } from "react"
import { useTranslation } from "react-i18next"
import { toast } from "sonner"

import { apiErrorText } from "@/api/translate-error"
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
  const { t } = useTranslation()
  const sectors = useSectors()
  const tables = useTables()
  const createSector = useCreateSector()

  const [name, setName] = useState("")
  const [color, setColor] = useState("#7c9cff")

  const addSector = () => {
    const trimmed = name.trim()
    if (!trimmed) {
      toast.error(t("settings.sectors.nameRequired"))
      return
    }
    const nextOrder = (sectors.data?.length ?? 0) + 1
    createSector.mutate(
      { name: trimmed, color, sort_order: nextOrder },
      {
        onSuccess: () => {
          setName("")
          toast.success(t("settings.sectors.created"))
        },
        onError: (e) =>
          toast.error(apiErrorText(e, t, t("settings.sectors.createError"))),
      }
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            {t("settings.sectors.sectorsTitle")}
          </h3>
          <p className="text-sm text-muted-foreground">
            {t("settings.sectors.sectorsDesc")}
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <Input
            placeholder={t("settings.sectors.namePlaceholder")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="max-w-[14rem]"
          />
          <input
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            aria-label={t("settings.sectors.colorAria")}
            className="h-9 w-12 cursor-pointer rounded-md border border-border bg-transparent p-1"
          />
          <Button variant="outline" onClick={addSector} disabled={createSector.isPending}>
            {t("settings.sectors.add")}
          </Button>
        </div>

        {sectors.isPending ? (
          <Spinner />
        ) : (sectors.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">
            {t("settings.sectors.empty")}
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
          <h3 className="text-sm font-semibold text-foreground">
            {t("settings.sectors.tablesTitle")}
          </h3>
          <p className="text-sm text-muted-foreground">
            {t("settings.sectors.tablesDesc")}
          </p>
        </div>
        {tables.isPending ? (
          <Spinner />
        ) : (tables.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">{t("settings.sectors.tablesEmpty")}</p>
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
  const { t } = useTranslation()
  const update = useUpdateSector()
  const remove = useDeleteSector()
  const [name, setName] = useState(sector.name)
  const [color, setColor] = useState(sector.color ?? "#7c9cff")
  const dirty = name.trim() !== sector.name || color !== (sector.color ?? "#7c9cff")

  const save = () => {
    if (!name.trim()) return
    update.mutate(
      { id: sector.id, input: { name: name.trim(), color, sort_order: sector.sort_order } },
      { onError: (e) => toast.error(apiErrorText(e, t, t("settings.sectors.saveError"))) }
    )
  }

  return (
    <li className="flex flex-wrap items-center gap-2 px-3 py-2.5">
      <input
        type="color"
        value={color}
        onChange={(e) => setColor(e.target.value)}
        aria-label={t("settings.sectors.colorOf", { name: sector.name })}
        className="h-8 w-10 shrink-0 cursor-pointer rounded-md border border-border bg-transparent p-1"
      />
      <Input value={name} onChange={(e) => setName(e.target.value)} className="max-w-[12rem]" />
      <div className="ml-auto flex items-center gap-2">
        {dirty ? (
          <Button size="sm" variant="outline" onClick={save} disabled={update.isPending}>
            {t("settings.sectors.save")}
          </Button>
        ) : null}
        <Button
          size="sm"
          variant="ghost"
          className="text-destructive"
          disabled={remove.isPending}
          onClick={() =>
            remove.mutate(sector.id, {
              onError: (e) => toast.error(apiErrorText(e, t, t("settings.sectors.deleteError"))),
            })
          }
        >
          {t("settings.sectors.delete")}
        </Button>
      </div>
    </li>
  )
}

function TableAssignRow({ table, sectors }: { table: TableDTO; sectors: SectorDTO[] }) {
  const { t } = useTranslation()
  const update = useUpdateTable()
  const [capacity, setCapacity] = useState(table.capacity != null ? String(table.capacity) : "")

  const assignSector = (sectorId: string) => {
    update.mutate(
      { tableId: table.id, patch: { sector_id: sectorId === "" ? null : sectorId } },
      { onError: (e) => toast.error(apiErrorText(e, t, t("settings.sectors.assignError"))) }
    )
  }

  const saveCapacity = () => {
    const raw = capacity.trim()
    const value = raw === "" ? null : Number(raw)
    if (value !== null && (!Number.isInteger(value) || value < 1)) {
      toast.error(t("settings.sectors.invalidCapacity"))
      setCapacity(table.capacity != null ? String(table.capacity) : "")
      return
    }
    if (value === table.capacity) return
    update.mutate(
      { tableId: table.id, patch: { capacity: value } },
      { onError: (e) => toast.error(apiErrorText(e, t, t("settings.sectors.saveError"))) }
    )
  }

  return (
    <li className="flex flex-wrap items-center gap-2 px-3 py-2.5">
      <span className="w-16 shrink-0 text-sm font-medium">
        {table.name ?? t("settings.sectors.tableName", { number: table.number })}
      </span>
      <select
        value={table.sector_id ?? ""}
        onChange={(e) => assignSector(e.target.value)}
        className="h-9 rounded-md border border-border bg-background px-2 text-sm"
      >
        <option value="">{t("settings.sectors.noSector")}</option>
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
          placeholder={t("settings.sectors.capacityPlaceholder")}
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
          onBlur={saveCapacity}
          className="w-20"
        />
        <span className="text-xs text-muted-foreground">{t("settings.sectors.covers")}</span>
      </div>
    </li>
  )
}
