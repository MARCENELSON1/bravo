# Wellnod · Landing

Landing pública de Wellnod (marketing + acceso). Proyecto **separado** de la app
(`bravo/frontend`), con su propio `package.json` y su propio servidor de desarrollo.

- **Stack:** React 19 + Vite + TypeScript + Tailwind v4.
- **Arquitectura:** Hexagonal (Ports & Adapters) + Clean Architecture, con SOLID.
- **Login/registro:** los botones enlazan a la app real (`/login` y `/onboarding`).
  La URL base se configura con `VITE_APP_URL` (ver `.env.example`).

## Cómo correrlo

```bash
cd bravo/landing
npm install
cp .env.example .env   # opcional: ajustá VITE_APP_URL
npm run dev            # http://localhost:5174
```

Otros scripts: `npm run build` (typecheck + build de producción), `npm run preview`,
`npm run typecheck`.

## Arquitectura

La **regla de oro**: las dependencias apuntan **hacia adentro**.
`presentation → application → domain ← infrastructure`.
El `domain` no importa React, ni Vite, ni ningún framework.

```
src/
├── domain/                      # Núcleo puro. Sin frameworks.
│   ├── entities/                #   Plan, Feature, Step, Integration, Faq
│   ├── value-objects/           #   Money (importe + moneda)
│   └── ports/                   #   Interfaces (contratos): PlanRepository,
│                                #   ContentRepository, LeadGateway
│
├── application/                 # Casos de uso. Dependen de los PUERTOS, no de adapters.
│   └── use-cases/               #   GetPricingPlans, GetLandingContent, SubmitLead
│
├── infrastructure/              # Adapters concretos que CUMPLEN los puertos.
│   ├── config/                  #   AppConfig (lee import.meta.env)
│   ├── repositories/            #   StaticPlanRepository, StaticContentRepository
│   ├── gateways/                #   ConsoleLeadGateway (sin backend por ahora)
│   └── di/                      #   container.ts → composition root (wiring)
│
└── presentation/                # UI React. Consume casos de uso vía contexto.
    ├── providers/               #   ContainerProvider (inyecta el contenedor)
    ├── hooks/                   #   usePricingPlans, useLandingContent, useLeadForm, useTheme…
    ├── lib/                     #   cn() (merge de clases)
    ├── components/
    │   ├── brand/               #   Isotipo + wordmark Wellnod
    │   ├── ui/                  #   Button, Reveal, ThemeToggle
    │   └── sections/            #   Navbar, Hero, Audience, UnifiedSystem, Features,
    │                            #   Showcase, HowItWorks, Integrations, Pricing, Faq,
    │                            #   Contact, FinalCta, Footer
    └── pages/                   #   LandingPage (compone las secciones)
```

### SOLID aplicado

- **SRP** — cada caso de uso / entidad / adapter tiene una sola responsabilidad.
- **OCP** — para pasar de datos estáticos a una API real, se agrega un nuevo adapter
  (p. ej. `HttpPlanRepository`) sin tocar casos de uso ni UI.
- **LSP** — todo adapter respeta el contrato de su puerto y es intercambiable.
- **ISP** — puertos chicos y enfocados (`PlanRepository` ≠ `ContentRepository`).
- **DIP** — `application` y `presentation` dependen de **abstracciones** (puertos);
  las implementaciones concretas se inyectan en `infrastructure/di/container.ts`.

### ¿Cómo conectar un backend más adelante?

1. Creá el adapter (p. ej. `infrastructure/repositories/http-plan-repository.ts`) que
   implemente `PlanRepository` haciendo `fetch`.
2. Cambiá **una línea** en `infrastructure/di/container.ts` para usarlo.
3. Nada de `domain`, `application` ni `presentation` necesita cambiar.

> Nota: la landing es 100% frontend. No modifica ni depende del backend existente.
