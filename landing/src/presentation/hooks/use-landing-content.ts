import { useEffect, useState } from "react"

import type { LandingContent } from "@/application/use-cases/get-landing-content"
import { useContainer } from "@/presentation/providers/container-provider"

const EMPTY: LandingContent = { features: [], steps: [], integrations: [], faqs: [] }

// Puente entre el caso de uso GetLandingContent y React.
export function useLandingContent() {
  const { getLandingContent } = useContainer()
  const [content, setContent] = useState<LandingContent>(EMPTY)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    getLandingContent.execute().then((result) => {
      if (alive) {
        setContent(result)
        setLoading(false)
      }
    })
    return () => {
      alive = false
    }
  }, [getLandingContent])

  return { ...content, loading }
}
