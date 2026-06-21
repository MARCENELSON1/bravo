# Plan: Fase UI — Consola operativa (CRM) con Cult UI

## Summary
Transformar el frontend de **rebanadas funcionales sueltas** (un card centrado por flujo, primitivos shadcn pelados, sin navegación persistente) en una **consola operativa estilo CRM**: un *app shell* con navegación por rol, **dashboard con KPIs en pesos**, vistas de lista/detalle, data tables, paneles laterales, command palette y estados (vacío/cargando/error) consistentes — **adoptando Cult UI** (registro `@cult-ui` vía el MCP de shadcn) como sistema de diseño, tal como define el `CLAUDE.md`. No agrega features de negocio nuevos: **re-presenta** todo lo ya construido (Fases 1→3.5) bajo una identidad visual cohesiva y una IA de navegación de producto, y deja el esqueleto listo para las capas que vienen (asesor, reportes, AFIP, stock, fichaje, clientes).

> **Objetivo de calidad (pedido explícito):** completo, **no básico**, contemplando **absolutamente todo** (todas las pantallas, todos los roles, todos los estados), manteniendo la **identidad de diseño** ya planteada y **arquitectado como un CRM**.

## Estado de implementación
PENDIENTE. Depende de Fases 1→3.5 (✅ en `main`). Se implementa en rama nueva `feat/fase-ui-crm`. Es un workstream de **presentación** (capa UI): no toca dominio/casos de uso/API del backend; sí consume endpoints existentes y puede pedir **agregados de lectura nuevos** (dashboard) — ver "Dependencias de backend".

## User Story
Como **dueño/encargado** quiero **una consola con todo mi local en un solo lugar — ventas del día, mesas, cocina, caja, equipo, integraciones — con una identidad cuidada y navegación clara**, y como **mozo/cocina/cajero** quiero **mi vista enfocada y táctil**, para **operar rápido y entender el negocio de un vistazo**, sin pantallas sueltas ni diseño improvisado.

## Problem → Solution
Hoy cada flujo es una página aislada (`/app/floor`, `/app/orders/:id`, `/app/kds`, …) con "Volver" y estilo mínimo; no hay shell, ni dashboard, ni patrones de CRM, ni Cult UI. → Se introduce un **AppShell** (sidebar + topbar + área de contenido) con navegación **adaptada por rol y por dispositivo**, un **design system** sobre Cult UI, y se **re-skinean** todas las pantallas con patrones de consola (tablas, filtros, sheets, command palette, skeletons, empty states). La arquitectura por capas (UI / estado / **datos inyectables**) se mantiene intacta.

---

## Visión & identidad de diseño (design language)

**Producto:** NÚCLEO — *"el cerebro del local"*: motor operativo (capturar) + inteligencia (asesorar). La UI debe sentirse como una **consola de operaciones moderna**: densa pero calma, rápida, con datos en **pesos primero**, en **español rioplatense**.

**Fundaciones ya presentes (honrarlas, no reinventar):**
- **Tipografía:** `Geist Variable` (sans + heading) — ya cargada (`@fontsource-variable/geist`).
- **Color:** paleta **OKLCH** neutral, **light + dark** vía `next-themes` (ya es dependencia). Tokens semánticos shadcn ya definidos: `background/foreground/card/popover/primary/secondary/muted/accent/destructive/border/input/ring`, **`sidebar-*`** y **`chart-1..5`** (⇒ el tema ya anticipa sidebar + dashboards).
- **Radios:** escala `--radius-sm…4xl` ya definida → usar consistentemente (cards 2xl, controles md/lg).
- **Motion:** `tw-animate-css` + animaciones de Cult UI (entradas sutiles, números que cuentan, transiciones de estado). Sobrio: nada que distraiga en operación.
- **Íconos:** `lucide-react`.
- **Acento de marca:** definir 1 color primario de NÚCLEO (chart/accent) — propuesta: un acento cálido único que conviva con el neutral; se decide al construir el theme (tarea T1). Mantener contraste AA.

**Tono visual:** superficies limpias, jerarquía por tamaño/peso (no por saturación), bordes sutiles, sombras suaves, foco visible. Modo **oscuro de primera clase** (cocina/operación nocturna).

---

## Principios de UX
1. **Rol primero:** cada rol entra a SU vista por defecto (mozo→floor, cocina→KDS, cajero→caja, owner/manager→dashboard). El shell muestra solo lo que el rol puede usar.
2. **Dispositivo correcto:** owner/manager = **desktop** (consola ancha); mozo = **tablet/mobile** (táctil); cocina = **tablet apaisada** (board, targets grandes, alto contraste).
3. **Dato accionable de un vistazo:** KPIs en pesos, badges de estado, totales siempre visibles.
4. **Sin callejones:** toda vista tiene **empty / loading (skeleton) / error / success** definidos.
5. **Teclado y velocidad:** command palette (Cmd/Ctrl-K) para navegar y disparar acciones; atajos en KDS/floor.
6. **Consistencia:** un solo set de componentes (Cult UI) y patrones; nada ad-hoc.

---

## Arquitectura de información (IA) + navegación por rol

**AppShell** = `Sidebar` (colapsable; drawer en mobile) + `Topbar` (marca + tenant, búsqueda/command-k, notificaciones, **toggle tema**, menú de usuario) + `Content` (page header con título + breadcrumbs + acciones, luego el cuerpo).

**Secciones del sidebar (agrupadas):**
- **Resumen** → Dashboard.
- **Operación** → Mesas (Floor), Comandas, Cocina (KDS), Caja.
- **Catálogo** → Productos. *(futuro: Stock/Insumos, Recetas)*.
- **Finanzas** → Egresos. *(futuro: Facturación AFIP, Reportes)*.
- **Inteligencia** *(placeholders "próximamente")* → Asesor/Copiloto, Reportes, Clientes (CRM).
- **Administración** → Equipo (usuarios/invitaciones), Integraciones (MercadoPago), Configuración del local.

**Visibilidad por rol (gating en el shell, además de las rutas):**
| Rol | Default | Ve |
|---|---|---|
| OWNER / MANAGER | Dashboard | todo |
| CASHIER | Caja | Caja, Mesas, Comandas (cobro) |
| WAITER | Mesas | Mesas, Comandas |
| KITCHEN | Cocina | Cocina (KDS) |

Items "próximamente" se muestran deshabilitados con etiqueta, para comunicar el roadmap sin romper.

---

## Inventario COMPLETO de pantallas (todo lo que entra)

### A. Identidad / acceso (re-skin con marca)
1. **Login** — split-screen con panel de marca (claim "el cerebro del local") + form; estados de error (incl. "verificá tu email"), loading.
2. **Onboarding** (alta de local) — wizard multipaso (datos del local → owner → país/moneda) con progreso.
3. **Verificar email** — estado con feedback (éxito/expirado/reenviar).
4. **Aceptar invitación** — set de contraseña + bienvenida.
5. **(nuevo) Recuperar / resetear contraseña** — si el flujo existe en backend, darle UI; si no, dejar el enganche.

### B. Shell & navegación (nuevo)
6. **AppShell** (sidebar + topbar + content) responsive.
7. **Command palette** (Cmd-K): navegar, "nueva comanda", "cobrar mesa N", "registrar egreso", cambiar tema.
8. **Selector de tema** claro/oscuro + densidad (cómoda/compacta).
9. **Menú de usuario** (perfil, rol, comercio, cerrar sesión).

### C. Resumen / inteligencia
10. **Dashboard** (owner/manager): KPIs en pesos del día (ventas, ticket promedio, comandas activas, cobrado vs pendiente, egresos, neto), **charts** (ventas por hora, medios de pago, top productos), accesos rápidos. *(usa tokens `chart-*`; números con "ticker").*
11. **(placeholder) Asesor / Reportes / Clientes** — pantallas "próximamente" con copy del roadmap (no funcionales aún).

### D. Operación
12. **Mesas (Floor)** — **mapa/grid de mesas** con estado (libre/abierta/por cobrar/pagada), total por mesa, acción "abrir/ir a comanda"; filtros por estado; responsive tablet.
13. **Comanda (Order detail)** — header con mesa/estado/mozo; **líneas de ítems** (agregar/editar/quitar, notas), total; acciones por estado (enviar a cocina, avanzar); **bloque Cobrar** (medio + monto, MP link/QR + polling a PAID, lista de pagos, badge PAGADA); hint "Conectá MercadoPago" si no está conectado.
14. **Cocina (KDS)** — **board por estado** (SENT→PREPARING→READY) con columnas, tickets grandes, contador de tiempo, acción táctil de avance; polling; modo alto contraste; apaisado/tablet.
15. **Caja (nuevo)** — cobros del día (tabla con medio/monto/comanda/estado), totales por medio, **arqueo** (efectivo vs electrónico), accesos a comandas por cobrar.

### E. Catálogo / finanzas
16. **Productos** — **data table** (nombre, precio en pesos, categoría, activo) con búsqueda/filtro/orden; alta/edición en **sheet**; activar/desactivar.
17. **Egresos** — **data table** (fecha, rubro, contraparte, medio, monto) con filtros; alta en sheet/modal; totales.

### F. Administración
18. **Equipo** — tabla de usuarios (email, rol, estado) + **invitar** (sheet con rol); reenviar/gestionar invitaciones.
19. **Integraciones** — MercadoPago (Conectar/estado/Desconectar) con la pantalla ya hecha, re-skineada; tarjeta lista para más pasarelas/AFIP.
20. **Configuración** — datos del local (nombre, slug, país/moneda — read/edit donde el backend lo permita), preferencias de la app (tema/densidad), zona de "peligro".

### G. Transversales (estados/edge)
21. **Loading** (skeletons por tipo de vista), **Empty states** (con ilustración/CTA), **Error/perm"403"** (ya existe RequireRole — re-skin), **404**, **offline/retry**, **toasts** (sonner re-estilados).

---

## Sistema de diseño / foundations
- **Theme tokens (T1):** consolidar `index.css` — acento de marca, ajustar `chart-*` a una paleta coherente, verificar contraste AA en light+dark, escala tipográfica (display/h1..h4/body/caption/mono para números), escala de spacing y de radios, sombras.
- **Tipografía de números:** tabular-nums + formato `es-AR` (ya existe `formatMoney`); KPIs con "number ticker" de Cult UI.
- **Densidad:** variante cómoda/compacta (atributo en el shell) para tablas.
- **Dark mode:** `next-themes` (class strategy ya: `@custom-variant dark`), toggle persistente + respeto a `prefers-color-scheme`.
- **Responsive/breakpoints:** mobile (mozo), md/tablet (floor/KDS), lg+/desktop (consola). Sidebar: full → iconos → drawer.
- **Motion:** transiciones de 150–250ms, entradas sutiles, respetar `prefers-reduced-motion`.
- **Layout primitives:** `PageHeader`, `Section`, `Toolbar`, `DataTable`, `DetailSheet`, `StatCard`, `EmptyState`, `Skeleton`, `StatusBadge`.

---

## Patrones CRM (a estandarizar)
- **AppShell** con navegación persistente + breadcrumbs + page header con acciones.
- **DataTable** reusable: búsqueda, filtros, orden, paginación/scroll, estados (loading/empty/error), acciones por fila, selección. (Productos, Egresos, Caja, Equipo.)
- **DetailSheet / Drawer** para alta/edición sin cambiar de ruta (forms con react-hook-form + zod ya en stack).
- **Command palette** (Cmd-K) global.
- **StatCard / KPI** con delta y mini-spark.
- **StatusBadge** por dominio (comanda OPEN/SENT/PREPARING/READY/SERVED/PAID/CANCELLED; pago PENDING/CONFIRMED/FAILED; conexión MP).
- **Confirmaciones** (dialog) para acciones destructivas (cancelar comanda, desconectar MP, desactivar producto).
- **Toasts** consistentes (sonner) para éxito/error de mutaciones.

---

## Adopción de Cult UI (vía MCP de shadcn — NO inventar componentes)
Regla del `CLAUDE.md`: **antes de codear a mano, buscar en Cult UI**. Flujo por cada necesidad de UI:
1. `mcp__shadcn__list_items_in_registries` / `search_items_in_registries` sobre `@cult-ui` para descubrir el catálogo real (cards animadas, bento grid, texture/gradient buttons, number ticker, sidebar/dock, command, dialog/sheet, tabs, etc.).
2. `mcp__shadcn__view_items_in_registries` + `get_item_examples_from_registries` para ver API/uso.
3. `mcp__shadcn__get_add_command_for_items` y agregarlo; envolverlo en nuestros primitivos (`components/ui`) para mantener consistencia.
4. Solo si Cult UI no lo tiene, componer sobre shadcn base (ya instalado: button, card, input, select, label, separator, sonner, spinner, field, **texture-button**).

> El **mapeo exacto componente↔pantalla** se completa en T2 consultando el MCP (no se hardcodea acá para no inventar nombres). Candidatos por función: **shell/sidebar**, **command**, **KPI/number-ticker**, **bento/stat cards** (dashboard), **animated card** (mesas), **table** (productos/egresos/caja/equipo), **sheet/drawer** (forms), **badge/tag** (estados), **dialog** (confirmaciones), **texture/gradient button** (acciones primarias).

---

## Arquitectura front (preservar capas)
- **UI** (componentes/pantallas) / **estado** (Context de auth + tema + densidad) / **datos** (clientes API inyectables vía `services-context` + hooks TanStack). **No** `fetch` suelto. Todo lo nuevo respeta esto.
- Rutas con `react-router-dom`; el AppShell es un **layout route** que envuelve a las protegidas; `RequireAuth`/`RequireRole` se mantienen.
- Componentes presentacionales puros + contenedores con hooks. Tests con Vitest/RTL para lógica de UI no trivial (shell por rol, command palette, data table).

## Dependencias de backend
- La mayoría reusa endpoints existentes (orders/products/tables/payments/expenses/integrations/users).
- **Dashboard/Caja** necesitan **agregados de lectura** (totales del día por medio, ventas por hora, top productos). Decisión: si no existen, se agregan como **read models / endpoints de reporting** ligeros (fuera de este plan de UI, o como sub-tarea de backend mínima). Mientras tanto, la UI puede derivar algunos KPIs del lado cliente a partir de listados — marcado como provisional.

---

## Files to Change (estructura propuesta)
| Área | Archivos (nuevos/!) |
|---|---|
| Theme | `frontend/src/index.css` (!), `frontend/src/lib/theme.ts` (densidad), `theme-provider`/toggle |
| Shell | `frontend/src/app/app-shell.tsx`, `components/shell/{sidebar,topbar,nav-config,user-menu,command-palette}.tsx`, `app/router.tsx` (!) |
| Primitivos | `components/ui/*` (Cult UI agregados), `components/patterns/{page-header,data-table,detail-sheet,stat-card,empty-state,status-badge,skeletons}.tsx` |
| Pantallas | re-skin de `features/{identity,floor,orders,kds,products,expenses,integrations}/*` + nuevos `features/{dashboard,caja,team,settings}/*` |
| Estado | `state/theme-context` + densidad; `auth` (ya) |
| Tests | `*.test.tsx` para shell-por-rol, command palette, data table, dashboard |
| Infra | `package.json` (deps de Cult UI que pida el MCP), nav config por rol |

## NOT Building
- **Features de negocio nuevos** (lógica): no se agrega dominio; solo presentación. (Caja/Dashboard pueden requerir endpoints de lectura — se acota aparte.)
- **Capas futuras funcionales**: Asesor/Copiloto, Reportes, Clientes/CRM, Stock, Fichaje, AFIP → solo **placeholders** "próximamente" en la nav.
- **Multi-idioma**: sigue español (la i18n se difiere).
- **Theming white-label por tenant**: difiere; un solo theme de marca por ahora.
- **Rediseño del backend**: cero cambios de contrato salvo endpoints de lectura acordados.

---

## Step-by-Step Tasks (tramos)
> Orden: foundations → shell → patrones → pantallas por prioridad operativa → pulido. Validar `tsc + eslint + test + build` por tramo. Cada pantalla: definir estados (loading/empty/error) antes de "terminar".

### T1 — Design system / theme
- Consolidar tokens (acento de marca, `chart-*`, contraste AA light+dark), tipografía/escala, densidad; `ThemeProvider` (next-themes) + toggle persistente; primitivos base (`page-header`, `status-badge`, `empty-state`, `skeleton`).
- **Validar:** build + un Storybook-lite/preview de tokens (o una página `/style` interna temporal).

### T2 — Catálogo Cult UI + patrones
- Relevar `@cult-ui` por el MCP; agregar y envolver los componentes elegidos; construir `DataTable`, `DetailSheet`, `StatCard`, `CommandPalette` reusables.
- **Validar:** tests de `DataTable` (orden/filtro/empty) + command palette (navegación).

### T3 — AppShell + navegación por rol
- `AppShell` (sidebar colapsable + topbar + content), `nav-config` por rol, breadcrumbs, user-menu, theme toggle, responsive (drawer en mobile). Rutas como layout. Default por rol.
- **Validar:** test "cada rol ve su nav y su default"; recorrer en desktop/tablet/mobile.

### T4 — Identidad / acceso (re-skin)
- Login (split + marca), Onboarding (wizard), Verify-email, Accept-invitation, (reset si aplica). Estados de error/carga.
- **Validar:** tests existentes de login siguen verdes + nuevos.

### T5 — Operación (lo más usado primero)
- **Floor** (mapa de mesas), **Comanda** (detalle + cobro re-skineado con polling/QR), **KDS** (board táctil), **Caja** (cobros del día + arqueo).
- **Validar:** flujo mozo→cocina→cobro de punta a punta; tablet.

### T6 — Catálogo / finanzas / admin
- **Productos** (data table + sheet), **Egresos** (data table + sheet), **Equipo** (usuarios + invitar), **Integraciones** (re-skin), **Configuración**.
- **Validar:** CRUD por tabla + sheets.

### T7 — Dashboard + inteligencia (placeholders) + pulido
- **Dashboard** (KPIs en pesos + charts; endpoints de lectura o derivación provisional), placeholders "próximamente", command palette completa, empty/error/404, micro-animaciones, `prefers-reduced-motion`, accesibilidad (focus, roles ARIA, contraste), QA responsive final.
- **Validar:** `tsc + eslint + test + build`; pasada de accesibilidad; revisión visual por capturas.

---

## Validation Gates
- **Por tramo:** `npm run typecheck && lint && test && build` (en `frontend/`).
- **Accesibilidad:** foco visible, navegación por teclado, contraste AA, `prefers-reduced-motion`, labels/roles ARIA.
- **Responsive:** desktop (consola), tablet apaisada (KDS/floor), mobile (mozo).
- **Regresión funcional:** todos los flujos existentes (login, comanda→cobro, KDS, productos, egresos, integraciones) siguen operativos.
- **Manual:** recorrido por rol (owner/manager/waiter/kitchen/cashier) en los 3 tamaños.

## Risks / Open
- **Alcance grande:** mitigar con tramos entregables (cada uno deja la app usable). Priorizar operación (T5) sobre dashboard (T7).
- **Cult UI vs nuestro contrato:** envolver siempre en `components/ui`/`patterns` para no acoplar pantallas al detalle del registro.
- **Dashboard necesita datos agregados:** decidir endpoints de reporting (mínimo backend) vs derivación cliente provisional — acordar antes de T7.
- **Cookie/auth sin cambios:** el shell no altera el flujo de sesión (access en memoria + refresh cookie).
- **Decisiones abiertas (a confirmar al arrancar):** color de acento de marca; nombre comercial (afecta logotipo/claim); densidad por defecto; si Caja/Dashboard entran con datos reales o provisional.
