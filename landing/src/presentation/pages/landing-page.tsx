import { Navbar } from "@/presentation/components/sections/navbar"
import { Hero } from "@/presentation/components/sections/hero"
import { Audience } from "@/presentation/components/sections/audience"
import { UnifiedSystem } from "@/presentation/components/sections/unified-system"
import { Features } from "@/presentation/components/sections/features"
import { Showcase } from "@/presentation/components/sections/showcase"
import { HowItWorks } from "@/presentation/components/sections/how-it-works"
import { Integrations } from "@/presentation/components/sections/integrations"
import { Pricing } from "@/presentation/components/sections/pricing"
import { Faq } from "@/presentation/components/sections/faq"
import { Contact } from "@/presentation/components/sections/contact"
import { FinalCta } from "@/presentation/components/sections/final-cta"
import { Footer } from "@/presentation/components/sections/footer"

export function LandingPage() {
  return (
    <div className="min-h-svh bg-background text-foreground">
      <Navbar />
      <main>
        <Hero />
        <Audience />
        <UnifiedSystem />
        <Features />
        <Showcase />
        <HowItWorks />
        <Integrations />
        <Pricing />
        <Faq />
        <Contact />
        <FinalCta />
      </main>
      <Footer />
    </div>
  )
}
