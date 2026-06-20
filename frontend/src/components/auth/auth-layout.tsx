import type { ReactNode } from "react"

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

// Split-screen shell reused by every identity screen. The brand panel is hidden
// on mobile; the form card is always centered.
export function AuthLayout({
  title,
  description,
  children,
  footer,
}: {
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-primary p-10 text-primary-foreground lg:flex">
        <div className="font-heading text-sm font-medium tracking-wide">BRAVO</div>
        <div>
          <h2 className="font-heading text-3xl leading-tight font-medium">El cerebro del local</h2>
          <p className="mt-3 max-w-sm text-sm text-primary-foreground/70">
            Comandas, cobros y tu copiloto en español, en un solo lugar.
          </p>
        </div>
        <div className="text-xs text-primary-foreground/50">© BRAVO</div>
      </aside>

      <main className="flex items-center justify-center bg-background p-6">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle className="text-lg">{title}</CardTitle>
            {description ? <CardDescription>{description}</CardDescription> : null}
          </CardHeader>
          <CardContent>{children}</CardContent>
          {footer ? (
            <CardFooter className="justify-center text-sm text-muted-foreground">
              {footer}
            </CardFooter>
          ) : null}
        </Card>
      </main>
    </div>
  )
}
