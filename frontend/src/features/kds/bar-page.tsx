import { StationBoard } from "@/features/kds/station-board"

// The bar board: only items routed to the BAR station (coffee, drinks), bumped
// per item — separate from the kitchen so each station sees just its own work.
export function BarPage() {
  return (
    <StationBoard
      station="BAR"
      title="Barra"
      subtitle="Ítems de barra (café, tragos) en preparación, en vivo."
    />
  )
}
