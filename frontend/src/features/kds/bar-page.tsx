import { useTranslation } from "react-i18next"

import { StationBoard } from "@/features/kds/station-board"

// The bar board: only items routed to the BAR station (coffee, drinks), bumped
// per item — separate from the kitchen so each station sees just its own work.
export function BarPage() {
  const { t } = useTranslation()
  return (
    <StationBoard
      station="BAR"
      title={t("kds.bar.title")}
      subtitle={t("kds.bar.subtitle")}
    />
  )
}
