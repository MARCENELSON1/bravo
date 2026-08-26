import { useTranslation } from "react-i18next"

import { StationBoard } from "@/features/kds/station-board"

// The kitchen board: only items routed to the KITCHEN station, bumped per item.
export function KdsPage() {
  const { t } = useTranslation()
  return (
    <StationBoard
      station="KITCHEN"
      title={t("kds.kitchen.title")}
      subtitle={t("kds.kitchen.subtitle")}
    />
  )
}
