import { Navbar } from "@/presentation/components/sections/navbar"
import { Hero } from "@/presentation/components/sections/hero"
import { Audience } from "@/presentation/components/sections/audience"
import { Features } from "@/presentation/components/sections/features"
import { Showcase } from "@/presentation/components/sections/showcase"
import { HowItWorks } from "@/presentation/components/sections/how-it-works"
import { Pricing } from "@/presentation/components/sections/pricing"
import { Contact } from "@/presentation/components/sections/contact"
import { FinalCta } from "@/presentation/components/sections/final-cta"
import { Footer } from "@/presentation/components/sections/footer"
import { SiteBackground } from "@/presentation/components/ui/site-background"

export function LandingPage() {
  return (
    <div className="min-h-svh text-foreground">
      <SiteBackground />
      <Navbar />
      <main>
        <Hero />
        <Audience />
        <Features />
        <Showcase />
        <HowItWorks />
        <Pricing />
        <Contact />
        <FinalCta />
      </main>
      <Footer />
    </div>
  )
}
