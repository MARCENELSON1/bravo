# Plan: App Mobile (Flutter) — Fase 0: Fundaciones

## Summary
Levantar el proyecto Flutter nativo en `mobile/` (aditivo, no toca `frontend/` ni `backend/`) con lo mínimo para que el equipo pueda **loguearse por rol y ver un Home** contra `api.wellnod.com`, con **paridad visual claro/oscuro** del shell glass. Resuelve el **riesgo #1 (auth móvil sin cookie)**, deja cableado el **`ThemeData` con los design tokens**, el **shell de navegación (bottom nav por rol)** y valida el **codegen OpenAPI→Dart** como spike. Sin backend changes: el backend ya soporta refresh por body.

## User Story
Como **miembro del equipo del local (mozo/cocina/caja/dueño)**, quiero **loguearme desde la app nativa y ver mi Home**, para que **la fundación (auth, tema, navegación) esté validada antes de sumar las pantallas operativas**.

## Problem → Solution
Hoy no existe app nativa (cero código Flutter en el repo) y el auth de la web depende de una cookie HttpOnly que un cliente nativo no maneja igual → **una app Flutter mínima que hace login (token-in-header), guarda el refresh en secure storage, refresca solo y pinta el Home con la identidad visual 1:1**.

## Metadata
- **Complexity**: **XL** (subsistema nuevo; scope de F0 acotado a fundaciones)
- **Source PRD**: `.claude/PRPs/prds/mobile-app.prd.md`
- **PRD Phase**: Fase 0 — Fundaciones
- **Estimated Files**: ~35 nuevos bajo `mobile/` (0 modificados fuera de `mobile/`)

---

## UX Design

### Before
`N/A` — no existe app mobile. La única experiencia mobile hoy es la web responsive en el navegador.

### After
```
┌───────────────────────────┐        ┌───────────────────────────┐
│  Splash (boot)            │        │  Home (mínimo)            │
│  ├ hay refresh guardado?  │        │  "Hola, {name}"           │
│  │   sí → refresh + /me   │  ───▶  │  {tenant_name} · {rol}    │
│  │   no → Login           │        │  ─────────────────────    │
│  Login                    │        │  [ Bottom nav por rol ]   │
│  slug · email · password  │        │  Home · (placeholders)    │
│  [ Ingresar ]             │        │  fondo glass claro/oscuro │
└───────────────────────────┘        └───────────────────────────┘
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Login | Web form en navegador | Pantalla nativa (slug+email+password) | mismo `POST /auth/login` form-urlencoded |
| Sesión | Cookie HttpOnly + access en memoria | Refresh en secure storage + access en memoria | token-in-header puro |
| Tema | `.dark` en `<html>` (next-themes) | `ThemeMode.system/light/dark` | mismos tokens (OKLCH→sRGB) |
| Navegación | Sidebar + rutas react-router | Bottom nav por rol (go_router) | role-landing espejado |

---

## Mandatory Reading

Leer ANTES de implementar (paths desde `/Users/marce/Desktop/BRAVO/`):

| Prioridad | Archivo | Líneas | Por qué |
|---|---|---|---|
| P0 | `frontend/src/api/http-client.ts` | 26-40, 48-59, 86-99, 113-155 | Patrón a espejar: puerto `HttpClient`, `Bearer`, `credentials:include`, single-flight 401→refresh, mapeo `ApiError` |
| P0 | `frontend/src/api/token-store.ts` | 1-19 | Access token SOLO en memoria (a replicar en Flutter) |
| P0 | `frontend/src/api/auth-api.ts` | 14-92 | login (OAuth2 password, slug en `client_id`), refresh, logout, me |
| P0 | `frontend/src/auth/auth-provider.tsx` | 16-76 | Boot = refresh silencioso + `/me`; estados booting/authenticated/anonymous |
| P0 | `frontend/src/index.css` | 1-221 | **Fuente única de tokens**: OKLCH `:root`/`.dark`, `--radius` 12px + multiplicadores, fuentes, glass, fondo escénico, scrollbars |
| P0 | `backend/app/presentation/api/v1/auth.py` | 29-109 | Contrato real de login/refresh/logout (form-urlencoded, cookie/body). NO modificar |
| P0 | `backend/tests/integration/test_e2e_auth.py` | 80-95 | Prueba viva de refresh **por body** `{"refresh_token": ...}` (habilita el móvil) |
| P1 | `frontend/src/auth/role-landing.tsx` | 8-20 | Ruteo inicial por rol (WAITER→floor, KITCHEN→kds, BAR→bar, CASHIER→floor?cobrar, OWNER/MANAGER→dashboard) |
| P1 | `frontend/src/auth/require-auth.tsx`, `require-role.tsx` | todas | Guards a espejar (auth gate + rol) |
| P1 | `frontend/src/api/translate-error.ts` | 17-22 | `apiErrorText` por `code` (ES vacío→message backend; EN mapea codes) |
| P1 | `frontend/src/i18n/index.ts` | 12-64 | Init i18n, selección de idioma, `localStorage["wellnod:lang"]`, fallback ES |
| P1 | `frontend/src/api/types.ts` | 3, 18-25 | `Role` union y `MeResponse` DTO |
| P1 | `backend/app/infrastructure/security/token_service.py` | 21-22, 29-66, 101-118 | Claims JWT, issuer/aud `bravo-api`, formato refresh opaco (contexto) |
| P2 | `frontend/src/components/shell/app-shell.tsx` | 45-47 | Valores glass del panel del shell |
| P2 | `frontend/src/components/ui/glass-card.tsx` | 10-13 | Valores glass de tarjeta |
| P2 | `frontend/src/components/shell/app-background.tsx` | 8-26 | Fondo escénico (hex EXACTOS del gradiente + texturas) |
| P2 | `frontend/src/services/services-provider.tsx` | 42-74 | Contenedor DI `Services` (referencia de organización) |
| P2 | `backend/app/config.py` | 32-82 | Nombres exactos de env (`ACCESS_TOKEN_TTL_MIN=15`, `REFRESH_TOKEN_TTL_DAYS=30`, `refresh_cookie_name=bravo_refresh`, `cookie_path=/api/v1/auth`, `cookie_secure=True`) |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| Riverpod (estado) | riverpod.dev (v2) | `ProviderScope` raíz; `NotifierProvider`/`AsyncNotifier` para sesión; override en tests (equivalente al DI del front) |
| dio (HTTP) | pub.dev/packages/dio (v5) | `Interceptor` para Bearer + refresh; `response.headers.map['set-cookie']` para leer el refresh |
| flutter_secure_storage | pub.dev (v9) | Keychain (iOS) / EncryptedSharedPreferences (Android) para el refresh token |
| go_router | pub.dev (v14) | `redirect` para el auth gate; rutas por rol; `StatefulShellRoute` para bottom nav |
| swagger_parser | pub.dev | Codegen Dart-native que **soporta OpenAPI 3.1** (ver GOTCHA) → modelos + cliente dio/retrofit |
| freezed + json_serializable | pub.dev | DTOs inmutables + `fromJson`; consistente con lo que emitirá el codegen |
| intl + flutter gen-l10n | docs.flutter.dev/ui/accessibility-and-internationalization | ARB por idioma, `es` fallback (paridad), `{x}` interpolación |
| shared_preferences | pub.dev | Persistir tema (`wellnod:theme`) e idioma (`wellnod:lang`) |
| OKLCH→sRGB | culori (npm) / oklch.com | Convertir los tokens del `index.css` a `Color(0xFF..)` con fidelidad (NO usar los hex aprox. directo) |

---

## Patterns to Mirror

### HTTP_PORT_AND_REFRESH
// SOURCE: frontend/src/api/http-client.ts:26-40,48-59,131-154
```ts
export interface HttpClient {
  request<T>(method: string, path: string, options?: RequestOptions): Promise<T>
}
// ...single-flight refresh:
if (response.status === 401 && options.auth && !path.startsWith(REFRESH_PATH)) {
  const refreshed = await this.tryRefresh()   // UNA sola promesa compartida
  if (refreshed) response = await this.send(method, path, options)
}
```
→ En Flutter: `abstract class ApiClient` + un `AuthInterceptor` (dio) que hace UN refresh a la vez (guardar `Future<bool>? _refreshing`) y reintenta la request una vez.

### ACCESS_TOKEN_IN_MEMORY
// SOURCE: frontend/src/api/token-store.ts:6-19
```ts
let accessToken: string | null = null
export function setAccessToken(t: string | null) { accessToken = t }
```
→ En Flutter: el access token vive en un `Notifier` en memoria; NUNCA en secure storage (solo el refresh se persiste).

### LOGIN_FORM_URLENCODED
// SOURCE: frontend/src/api/auth-api.ts (login) + backend/app/presentation/api/v1/auth.py:66-79
```ts
// El slug del tenant viaja en client_id (OAuth2PasswordRequestForm)
this.http.request("POST", "/auth/login", { form: { username: email, password, client_id: slug } })
```
→ En Flutter (dio): `Options(contentType: Headers.formUrlEncodedContentType)`, body `{"username": email, "password": pass, "client_id": slug}`. La respuesta trae `access_token` en el body y `bravo_refresh` en `Set-Cookie`.

### BOOT_SEQUENCE
// SOURCE: frontend/src/auth/auth-provider.tsx:48-76
```ts
await authApi.refresh()          // silencioso, contra el token guardado
const me = await authApi.me()    // hidrata la sesión
```
→ En Flutter: `SessionNotifier.boot()` = si hay refresh en secure storage → refresh + `/me`; si no o falla → estado `anonymous`.

### ROLE_LANDING
// SOURCE: frontend/src/auth/role-landing.tsx:8-20
```ts
WAITER → /app/floor ; KITCHEN → /app/kds ; BAR → /app/bar ;
CASHIER → /app/floor?cobrar=1 ; OWNER|MANAGER → dashboard
```
→ En Flutter: la tab inicial del bottom nav depende del rol (en F0, todas menos Home son placeholders).

### DESIGN_TOKENS
// SOURCE: frontend/src/index.css:54-121 (extracto)
```css
:root { --primary: oklch(0.63 0.14 163); --background: oklch(1 0 0);
        --radius: 0.75rem; /* 12px, multiplicadores 0.6/0.8/1.0/1.4/1.8/2.2/2.6 */ }
.dark { --primary: oklch(0.7 0.16 163); --background: oklch(0.16 0.008 165); }
```
→ En Flutter: `WellnodColors` (light/dark) con los OKLCH convertidos a sRGB; `WellnodRadii` con base 12.0; dos `ColorScheme` → `ThemeData`.

### ERROR_BY_CODE
// SOURCE: frontend/src/api/translate-error.ts:17-22
```ts
if (isApiError(error)) return t(`errors.${error.code}`, { defaultValue: error.message })
```
→ En Flutter: `apiErrorText(ApiError e)` = intenta `errors.<code>` del ARB; si no existe, usa `e.message` (el texto español del backend). ES arranca vacío (paridad), EN mapea los codes que necesite F0 (login).

### GLASS_PANEL
// SOURCE: frontend/src/components/shell/app-shell.tsx:45-47 + glass-card.tsx:10-13
```
claro: bg white @60% + border black @10% + backdrop-blur-2xl (~40px) + rounded 16px
oscuro: bg black @30% (card: white @4.5%) + border white @10% + shadow
```
→ En Flutter: widget `GlassPanel` = `ClipRRect(BorderRadius 16) > BackdropFilter(ImageFilter.blur(sigma≈18)) > Container(color: white.withOpacity(.6)/black.withOpacity(.3), border)`.

### SCENIC_BACKGROUND
// SOURCE: frontend/src/components/shell/app-background.tsx:8-26 (hex EXACTOS)
```
claro: radial(125% 125% at 18% 12%) #d7e6df 0% → #aec7bb 50% → #85a394 100%
oscuro: #2a4b43 0% → #16241f 52% → #0a120e 100%
+ textura /app-bg-{light,dark}.png @50% soft-light + grano SVG @18% overlay
```
→ En Flutter: `AppBackground` con `RadialGradient` (hex exactos) + `Image.asset` de las texturas (copiar los PNG de `frontend/public/`).

---

## Files to Change

Todo bajo `mobile/` (NUEVO). Cero archivos modificados fuera de `mobile/`.

| Archivo | Acción | Justificación |
|---|---|---|
| `mobile/pubspec.yaml` | CREATE | Deps: flutter_riverpod, dio, flutter_secure_storage, go_router, intl, shared_preferences; dev: swagger_parser, freezed, json_serializable, build_runner, flutter_lints |
| `mobile/.gitignore` | CREATE | Patrones Dart/Flutter (`.dart_tool/`, `build/`, `.flutter-plugins*`, `ios/Pods/`, `*.iml`) — el raíz no los tiene |
| `mobile/analysis_options.yaml` | CREATE | `flutter_lints` |
| `mobile/l10n.yaml` + `mobile/lib/l10n/app_{es,en}.arb` | CREATE | i18n, `es` fallback |
| `mobile/lib/main.dart` | CREATE | `ProviderScope` + `WellnodApp` |
| `mobile/lib/env/env.dart` | CREATE | `apiBaseUrl` por `--dart-define` (default `http://localhost:8000/api/v1`; prod configurable) — espeja `lib/env.ts` |
| `mobile/lib/theme/colors.dart` | CREATE | `WellnodColors` light/dark (OKLCH→sRGB) |
| `mobile/lib/theme/radii.dart` | CREATE | Base 12.0 + multiplicadores |
| `mobile/lib/theme/theme.dart` | CREATE | `buildLightTheme()`/`buildDarkTheme()` (`ThemeData` + `ColorScheme` + fuentes) |
| `mobile/lib/theme/theme_controller.dart` | CREATE | `ThemeMode` provider + persistencia (`wellnod:theme`) |
| `mobile/assets/fonts/*` | CREATE | Geist Variable + Inter Variable (.ttf) |
| `mobile/assets/img/app-bg-{light,dark}.png` | CREATE | Copiados de `frontend/public/` |
| `mobile/lib/ui/glass_panel.dart` | CREATE | Widget glass reutilizable |
| `mobile/lib/ui/app_background.dart` | CREATE | Fondo escénico |
| `mobile/lib/api/api_client.dart` | CREATE | dio + base URL + `AuthInterceptor` |
| `mobile/lib/api/auth_interceptor.dart` | CREATE | Bearer + single-flight 401→refresh |
| `mobile/lib/api/api_error.dart` | CREATE | `ApiError{code,message,status}` (espeja `api-error.ts`) |
| `mobile/lib/auth/token_store.dart` | CREATE | access en memoria + refresh en `flutter_secure_storage` |
| `mobile/lib/auth/auth_repository.dart` | CREATE | login/refresh/logout/me (captura `Set-Cookie` en login/refresh) |
| `mobile/lib/auth/dtos.dart` | CREATE | `MeResponse`, `AccessTokenResponse` (freezed/json_serializable) |
| `mobile/lib/auth/session.dart` + `session_notifier.dart` | CREATE | `Session{userId,tenantId,role,email,name,tenantName}` + estados booting/authenticated/anonymous |
| `mobile/lib/router/router.dart` | CREATE | go_router + `redirect` (auth gate) + role-landing |
| `mobile/lib/features/login/login_page.dart` | CREATE | slug+email+password → `AuthRepository.login` |
| `mobile/lib/features/shell/app_scaffold.dart` | CREATE | Bottom nav por rol (`StatefulShellRoute`) + `AppBackground` |
| `mobile/lib/features/home/home_page.dart` | CREATE | Home mínimo (saludo desde `/me`) |
| `mobile/lib/api/generated/**` | CREATE | Spike codegen (subset `orders`/`tables`) — valida toolchain, no se consume aún |
| `mobile/test/**` | CREATE | Tests de token_store, auth_interceptor (refresh single-flight), apiErrorText, session boot |
| `mobile/README.md` | CREATE | Cómo correr, `--dart-define`, codegen, gotchas |

## NOT Building

- Piso, Comanda, KDS, Caja ni ninguna pantalla operativa (son F1+). En F0 esas tabs del bottom nav son **placeholders**.
- Modo contingencia offline / cola local / impresión ESC/POS (F1).
- Push, cámara/QR (F1+).
- Codegen de **toda** la superficie (37 routers). F0 solo valida el pipeline sobre 1-2 tags; el auth de F0 va **hand-written** (login form-urlencoded + captura de `Set-Cookie` no se codegenan bien).
- Cualquier cambio en `backend/` o `frontend/`. F0 es puramente aditivo en `mobile/` (el backend ya soporta refresh por body).
- Publicación en stores (solo correr en simuladores/dispositivos/TestFlight/Play Internal manual).

---

## Step-by-Step Tasks

### Task 1: Scaffold del proyecto Flutter
- **ACTION**: `flutter create --org com.wellnod --platforms ios,android mobile` (desde la raíz del repo).
- **IMPLEMENT**: dejar `mobile/` con estructura estándar; agregar `mobile/.gitignore` (Dart/Flutter) y `analysis_options.yaml` (`include: package:flutter_lints/flutter.yaml`).
- **GOTCHA**: NO tocar el `.gitignore` raíz; crear uno propio en `mobile/`. Confirmar que `flutter --version` usa un canal estable (3.2x+).
- **VALIDATE**: `cd mobile && flutter analyze` → 0 issues; `flutter test` (el test de ejemplo pasa).

### Task 2: Dependencias
- **ACTION**: agregar al `pubspec.yaml` las deps de runtime y dev (ver Files to Change).
- **IMPLEMENT**: `flutter pub get`.
- **VALIDATE**: `flutter pub get` sin conflictos; `flutter analyze` limpio.

### Task 3: Design tokens → ColorScheme
- **ACTION**: convertir los OKLCH de `index.css` a sRGB y crear `theme/colors.dart` (light+dark).
- **IMPLEMENT**: convertir con culori/oklch.com los tokens `--background/--foreground/--card/--primary/--secondary/--muted/--accent/--destructive/--border/--input/--ring` (light `:root` y dark `.dark`). Verde primario ≈ `#12a077` (light) / `#18b98c` (dark) — **verificar conversión exacta**. `border/input` en dark son blanco con alpha (8%/12%).
- **MIRROR**: `DESIGN_TOKENS`.
- **GOTCHA**: los hex del agente son **aproximados**; convertir con precisión. Los ÚNICOS hex literales exactos son los del fondo escénico (`app-background.tsx`).
- **VALIDATE**: capturas light/dark del Home comparadas contra la web (revisión visual).

### Task 4: Radios, fuentes y ThemeData
- **ACTION**: `theme/radii.dart` (base `12.0`, multiplicadores 0.6/0.8/1.0/1.4/1.8/2.2/2.6) y `theme/theme.dart`.
- **IMPLEMENT**: copiar los `.ttf` variables de Geist e Inter a `mobile/assets/fonts/` (desde `frontend/node_modules/@fontsource-variable/{geist,inter}` o Google Fonts), declararlos en `pubspec.yaml`; `fontFamily: 'Geist'`, display `Inter`. Construir `buildLightTheme()/buildDarkTheme()` con los `ColorScheme` de Task 3.
- **GOTCHA**: las fuentes son **variables** — usar el archivo variable y (opcional) `fontVariations`. Licencia OFL, ok para bundlear.
- **VALIDATE**: `flutter analyze`; el texto usa Geist, títulos Inter.

### Task 5: Glass + fondo escénico
- **ACTION**: `ui/glass_panel.dart` y `ui/app_background.dart`.
- **IMPLEMENT**: `GlassPanel` = `ClipRRect` + `BackdropFilter(ImageFilter.blur(sigmaX:18,sigmaY:18))` + `Container` con color alpha (light white@60% / dark black@30%; card white@4.5%) y borde alpha. `AppBackground` = `RadialGradient` con los hex exactos + `Image.asset` de las texturas @ opacidad 50%.
- **MIRROR**: `GLASS_PANEL`, `SCENIC_BACKGROUND`.
- **GOTCHA**: `BackdropFilter` sin `ClipRRect` sangra fuera del borde redondeado; siempre clip. En Android gama baja, blur alto cuesta — mantener sigma ≈15-20.
- **VALIDATE**: se ve el panel frosted sobre el fondo, en ambos temas.

### Task 6: Secure storage + token store
- **ACTION**: `auth/token_store.dart`.
- **IMPLEMENT**: access token en memoria (variable en un Notifier); refresh token en `flutter_secure_storage` bajo la key `wellnod_refresh`. Métodos `readRefresh/writeRefresh/clear`.
- **MIRROR**: `ACCESS_TOKEN_IN_MEMORY`.
- **GOTCHA**: en Android configurar `AndroidOptions(encryptedSharedPreferences: true)`. El refresh es **single-use** (rota en cada refresh) → siempre persistir el nuevo.
- **VALIDATE**: test unit: escribir/leer/clear del refresh (fake storage).

### Task 7: dio + ApiError + AuthInterceptor (single-flight refresh) — riesgo #1
- **ACTION**: `api/api_client.dart`, `api/api_error.dart`, `api/auth_interceptor.dart`.
- **IMPLEMENT**: dio con `baseUrl = Env.apiBaseUrl`. Interceptor: agrega `Authorization: Bearer <access>` si la request es autenticada; ante `401` (y no es `/auth/refresh`) hace **UN** refresh compartido (`Future<bool>? _refreshing`) y reintenta una vez; si falla, `tokenStore.clear()` + emite "unauthorized" (la sesión pasa a anonymous). Mapear toda respuesta no-2xx a `ApiError{code,message,status}` leyendo `{code,message}` del body.
- **MIRROR**: `HTTP_PORT_AND_REFRESH`, `ERROR_BY_CODE`.
- **GOTCHA**: no adjuntar Bearer al login/refresh. El backend responde `{code,message}` (`errors.py`); `code` es inglés estable, `message` español.
- **VALIDATE**: test unit con `DioAdapter`/mock: dos requests concurrentes que reciben 401 disparan **un solo** refresh y ambas reintentan.

### Task 8: AuthRepository (login/refresh/me/logout) — captura de Set-Cookie
- **ACTION**: `auth/auth_repository.dart` + `auth/dtos.dart`.
- **IMPLEMENT**:
  - `login(slug,email,password)`: `POST /auth/login` form-urlencoded (`username,password,client_id=slug`). Guardar `access_token` (body) en memoria y **extraer `bravo_refresh` del header `set-cookie`** → `tokenStore.writeRefresh`.
  - `refresh()`: `POST /auth/refresh` JSON `{"refresh_token": <guardado>}`; guardar nuevo access (body) y el **nuevo** `bravo_refresh` (Set-Cookie rotado).
  - `me()`: `GET /me` (Bearer) → `MeResponse`.
  - `logout()`: `POST /auth/logout` JSON `{"refresh_token": <guardado>}` + `tokenStore.clear()`.
- **MIRROR**: `LOGIN_FORM_URLENCODED`, contrato de `backend/.../auth.py:29-109`.
- **GOTCHA**: el refresh **solo** llega por `Set-Cookie` (nunca en el body), en login y en refresh → parsear el header cada vez. En dev contra `http://localhost:8000`, `COOKIE_SECURE=True` no impide leer el header en un cliente nativo (Approach A no usa cookie jar). Alternativa (Approach B, no elegida): `dio_cookie_manager`+`PersistCookieJar`.
- **VALIDATE**: `test_e2e_auth.py:80-95` es la prueba viva del contrato; test unit del repo con respuestas mockeadas (login setea refresh desde Set-Cookie; refresh rota).

### Task 9: Session + boot (Riverpod)
- **ACTION**: `auth/session.dart`, `auth/session_notifier.dart`.
- **IMPLEMENT**: `Session{userId,tenantId,role,email,name,tenantName}`; `SessionState = booting|authenticated(Session)|anonymous`. `boot()`: si hay refresh guardado → `refresh()`+`me()` → authenticated; si no o error → anonymous. Escuchar el "unauthorized" del interceptor → anonymous.
- **MIRROR**: `BOOT_SEQUENCE`.
- **GOTCHA**: `Role` enum = `OWNER,MANAGER,WAITER,KITCHEN,BAR,CASHIER` (incluye **BAR**).
- **VALIDATE**: test: boot con refresh válido → authenticated; sin refresh → anonymous.

### Task 10: Router + guards + role-landing (go_router)
- **ACTION**: `router/router.dart`.
- **IMPLEMENT**: `redirect` global: si `booting`→splash; si `anonymous` y ruta protegida→`/login`; si `authenticated` y en `/login`→landing por rol. `StatefulShellRoute` para el bottom nav.
- **MIRROR**: `ROLE_LANDING`, `require-auth.tsx`/`require-role.tsx`.
- **VALIDATE**: navegar login↔home según estado; rol define la tab inicial.

### Task 11: Shell (bottom nav por rol) + Home mínimo
- **ACTION**: `features/shell/app_scaffold.dart`, `features/home/home_page.dart`, `features/login/login_page.dart`.
- **IMPLEMENT**: `AppScaffold` con `AppBackground` + `NavigationBar` cuyas tabs dependen del rol (mozo: Home·Piso·Caja·Más; cocina: Home·Cocina·Más; dueño: Home·Finanzas·Más — todas menos Home son placeholders en F0). `HomePage`: `GlassPanel` con "Hola, {name}", `{tenant_name} · {rol}` (traducido) y un `ThemeMode` toggle. `LoginPage`: campos slug/email/password + errores vía `apiErrorText`.
- **MIRROR**: `GLASS_PANEL`, `common.roles.*` del i18n.
- **VALIDATE**: login real → Home con datos de `/me`; toggle claro/oscuro funciona.

### Task 12: i18n (ES/EN)
- **ACTION**: `l10n.yaml`, `lib/l10n/app_es.arb`, `app_en.arb`, wiring en `WellnodApp`.
- **IMPLEMENT**: `flutter_localizations` + gen-l10n; claves mínimas F0 (`login.*`, `home.*`, `common.roles.*`, algunos `errors.*` de login en EN). `es` = fallback; persistir idioma en `wellnod:lang` (misma key que la web).
- **MIRROR**: `frontend/src/i18n/index.ts` (fallback ES, key de storage), `translate-error.ts` (ES vacío→message backend).
- **GOTCHA**: ARB usa `{x}` (no `{{x}}`). No traducir todo: solo lo de F0.
- **VALIDATE**: cambiar idioma en runtime; los errores del backend se muestran (ES) o se mapean (EN).

### Task 13: Codegen OpenAPI→Dart (spike de validación)
- **ACTION**: configurar `swagger_parser` para generar modelos+cliente de 1-2 tags (`tables`, `orders`) desde `/openapi.json`.
- **IMPLEMENT**: bajar el schema del backend local (`curl http://localhost:8000/openapi.json > mobile/tool/openapi.json`), config de `swagger_parser` (output `lib/api/generated/`), `dart run swagger_parser`. Documentar el comando en `mobile/README.md`.
- **GOTCHA (importante)**: OpenAPI **3.1.0**. `swagger_parser` lo soporta; `openapi-generator` (dart-dio) históricamente cojea con 3.1 → si se usara, bajar el schema a 3.0 primero. Confirmar que lo generado **compila** (`flutter analyze`). No conectar aún al app (F1 lo consume).
- **VALIDATE**: `flutter analyze` limpio incluyendo `lib/api/generated/`; existe al menos un modelo generado usable.

### Task 14: Correr en iOS + Android + README
- **ACTION**: correr en simulador iOS y emulador Android contra el backend local; escribir `mobile/README.md`.
- **IMPLEMENT**: `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1` (Android emulador usa `10.0.2.2` para el localhost del host; iOS usa `localhost`). Levantar backend (`poetry run uvicorn app.main:app --reload`). Documentar `--dart-define`, codegen y gotchas.
- **GOTCHA**: Android emulador NO ve `localhost` del host → `10.0.2.2`. Si se usara Approach B (cookie), en dev http habría que `COOKIE_SECURE=False`; con Approach A no hace falta.
- **VALIDATE**: login real por rol en ambas plataformas; Home con datos reales; paridad visual claro/oscuro.

---

## Testing Strategy

### Unit Tests
| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| token_store rw | writeRefresh → readRefresh | mismo valor; clear→null | no |
| auth_interceptor single-flight | 2 requests concurrentes → 401 | 1 solo `/auth/refresh`, ambas reintentan | sí |
| auth_interceptor refresh falla | 401 + refresh 401 | sesión → anonymous, no loop | sí |
| auth_repository login | 200 + `Set-Cookie: bravo_refresh=X` | access en memoria, refresh=X persistido | sí |
| auth_repository refresh rota | refresh → nuevo Set-Cookie=Y | refresh persistido = Y | sí |
| apiErrorText | ApiError(code='invalid_credentials') | EN: texto mapeado; ES: message backend | sí |
| session boot | refresh guardado válido / ausente | authenticated / anonymous | sí |

### Edge Cases Checklist
- [ ] Sin refresh guardado (primer arranque) → login
- [ ] Refresh expirado/revocado (401 en refresh) → anonymous, sin loop
- [ ] Credenciales inválidas → `apiErrorText` muestra el mensaje
- [ ] Access vencido a mitad de sesión → refresh transparente + reintento
- [ ] Sin red → error claro (no crash)
- [ ] Rol BAR/CASHIER → tab inicial correcta

---

## Validation Commands

### Static Analysis
```bash
cd mobile && flutter analyze
```
EXPECT: Zero issues (incluyendo `lib/api/generated/`)

### Unit Tests
```bash
cd mobile && flutter test
```
EXPECT: All tests pass

### Codegen (build_runner + swagger_parser)
```bash
cd mobile && dart run build_runner build --delete-conflicting-outputs && dart run swagger_parser
```
EXPECT: genera modelos, `flutter analyze` sigue limpio

### Build (ambas plataformas)
```bash
cd mobile && flutter build apk --debug && flutter build ios --no-codesign --debug
```
EXPECT: build OK en Android e iOS

### Manual Validation
- [ ] Backend local corriendo (`poetry run uvicorn app.main:app --reload`)
- [ ] `flutter run` (iOS sim + Android emu con `10.0.2.2`) → login por rol → Home con `/me`
- [ ] Toggle claro/oscuro y cambio de idioma en runtime
- [ ] Matar la app y reabrir → sesión persiste (refresh en secure storage) → entra directo al Home
- [ ] Comparación visual del Home vs la web (light/dark)

---

## Acceptance Criteria
- [ ] Proyecto `mobile/` corre en iOS y Android
- [ ] Login por rol (slug+email+password) real contra el backend, token-in-header
- [ ] Refresh en secure storage + renovación transparente 401→refresh (single-flight)
- [ ] Sesión persiste entre reinicios; logout limpia el refresh
- [ ] `ThemeData` con tokens del `index.css`, claro/oscuro, glass y fondo escénico
- [ ] Bottom nav por rol + Home mínimo con datos de `/me`
- [ ] i18n ES/EN con fallback ES y errores por `code`
- [ ] Codegen OpenAPI→Dart validado (subset compila)
- [ ] `flutter analyze` 0 issues, `flutter test` verde
- [ ] Cero archivos modificados fuera de `mobile/`

## Completion Checklist
- [ ] Sigue los patrones del front (puerto HTTP, access en memoria, single-flight, error por code)
- [ ] No se tocó `backend/` ni `frontend/` (ni `auth.py`/`me.py`)
- [ ] Tests cubren token store, interceptor, repo, boot
- [ ] Sin valores hardcodeados (base URL por `--dart-define`)
- [ ] README con run/codegen/gotchas
- [ ] Autocontenido — no hizo falta buscar en el código durante la implementación

## Risks
| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Refresh solo por Set-Cookie (login) | M | Alto (auth) | Parsear `set-cookie` en login y refresh; contrato probado en `test_e2e_auth.py` |
| Codegen con OpenAPI 3.1 | M | Medio | `swagger_parser` (soporta 3.1); fallback: bajar schema a 3.0. Auth F0 va hand-written |
| Fidelidad OKLCH→sRGB | M | Medio (marca) | Conversión precisa con culori + revisión visual por tema |
| Fuentes variables en Flutter | B | Bajo | Bundlear .ttf variable; fallback system stack |
| Android emu no ve localhost | B | Bajo | `10.0.2.2` documentado |
| `COOKIE_SECURE`/HTTPS en prod | B | Medio | Approach A (body) evita depender de la cookie; prod ya es HTTPS |

## Notes
- **Riesgo #1 resuelto en diseño**: el backend ya acepta refresh por body (`auth.py:55-63`), así que F0 no requiere cambios de backend. El único trabajo fino es capturar `bravo_refresh` del `Set-Cookie` en login/refresh.
- **Decisiones de fierro (del PRD, confirmables acá)**: estado=Riverpod, HTTP=dio, storage=flutter_secure_storage, router=go_router, codegen=swagger_parser, DTOs=freezed/json_serializable.
- **Fuente de tokens**: `frontend/src/index.css` es la única verdad; cualquier drift futuro se re-porta desde ahí.
- Próximo: `/prp-implement .claude/PRPs/plans/mobile-fase-0-fundaciones.plan.md`.
