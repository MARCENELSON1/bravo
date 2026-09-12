# Wellnod Mobile (Flutter)

App nativa para el **equipo y el dueño del local** (mozo/cocina/caja/dueño), cliente
de la API FastAPI de Wellnod. Capa **aditiva** en `mobile/` — no toca `frontend/` ni
`backend/`. El comensal **no** usa esta app (sigue la Carta QR web/PWA).

> Estado: **Fase 0 — Fundaciones** (auth móvil, tema, navegación por rol, Home mínimo).
> Plan: `../.claude/PRPs/plans/mobile-fase-0-fundaciones.plan.md`.
> PRD: `../.claude/PRPs/prds/mobile-app.prd.md`.

## Requisitos

- Flutter 3.47+ (stable), Dart 3.13+.
- iOS: Xcode + CocoaPods. Android: Android Studio + SDK (para correr en Android).
- El backend corriendo (local o `api.wellnod.com`).

## Correr

La base URL de la API se pasa por `--dart-define` (default `http://localhost:8000/api/v1`):

```bash
# Backend local (desde ../backend): poetry run uvicorn app.main:app --reload

# iOS simulator / macOS  → localhost
flutter run --dart-define=API_BASE_URL=http://localhost:8000/api/v1

# Android emulador → 10.0.2.2 (el emulador NO ve el localhost del host)
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1

# Producción
flutter run --dart-define=API_BASE_URL=https://api.wellnod.com/api/v1
```

Login: **slug del local + email + contraseña** (el slug viaja en `client_id`, OAuth2
password flow). El refresh token se guarda en secure storage; la sesión persiste
entre reinicios.

## Validar

```bash
flutter analyze     # 0 issues
flutter test        # unit tests (cookie parse, roles, errores)
```

## Arquitectura (cliente fino)

- `lib/env/` — base URL por `--dart-define` (espeja `frontend/src/lib/env.ts`).
- `lib/theme/` — `ThemeData` con los tokens portados de `frontend/src/index.css`
  (OKLCH→sRGB gamut-mapped). Claro/oscuro/sistema, persistido.
- `lib/ui/` — `GlassPanel` (frosted) y `AppBackground` (gradiente escénico).
- `lib/api/` — `Dio` + `AuthInterceptor` (single-flight 401→refresh) + `ApiError`.
- `lib/auth/` — `TokenStore` (access en memoria, refresh en secure storage),
  `AuthRepository` (login/refresh/me/logout), `SessionNotifier` (Riverpod).
- `lib/router/` — `go_router` con guards (booting→splash, anónimo→login, auth→app).
- `lib/features/` — login, shell (bottom nav por rol), home.
- `lib/l10n/` — i18n ES/EN mínimo (fallback ES).

### Auth móvil (riesgo #1, resuelto)

El backend ya acepta el refresh **por body** (`{"refresh_token": ...}`) — sin cambios
de backend. El único detalle: el refresh token llega SOLO por `Set-Cookie:
bravo_refresh=...` (en login y en cada refresh rotado), así que el cliente lo
extrae de la cabecera y lo persiste (`lib/auth/refresh_cookie.dart`).

## Follow-ups de F0

- **Fuentes de marca**: bundlear Geist (sans/heading) e Inter (display) `.ttf`
  variables en `assets/fonts/` y setear `fontFamily` en `lib/theme/theme.dart`
  (hoy usa el stack del sistema).
- **Codegen OpenAPI→Dart** (spike): con el backend arriba,
  `curl http://localhost:8000/openapi.json` y generar con `swagger_parser`
  (soporta OpenAPI 3.1) hacia `lib/api/generated/`. Lo consume F1.
- **Android**: instalar Android Studio + SDK para `flutter run` en Android.
- Tests de integración del interceptor/refresh con un `MockAdapter` de Dio.
