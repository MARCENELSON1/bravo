import { StationBoard } from "@/features/kds/station-board"

// The kitchen board: only items routed to the KITCHEN station, bumped per item.
export function KdsPage() {
  return (
    <StationBoard
      station="KITCHEN"
      title="Cocina (KDS)"
      subtitle="Ítems de cocina en preparación, en vivo."
    />
  )
}
